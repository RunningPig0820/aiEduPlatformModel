"""
RAG 项目介绍助手 API - 白盒链路端点(Python 无状态引擎, B 组)

- POST /api/rag/assistant/ask       SSE 流式(事件时序冻结) + 非流式(done + stages 摘要)
- GET  /api/rag/assistant/guide     开始引导(静态池 RAG 定向, 0 token, 非 SSE)
- GET  /api/rag/assistant/eval/report  baseline 报告白盒(hit@3/质量分/成本/耗时)

对齐: openspec/changes/rag-project-intro-assistant-python/api.md(事件时序冻结)
     **permission 由 Java 网关产**(角色门在 Java); Python 生产端点不产 permission, 从 intent 开始。
鉴权: x-internal-token(同 api/chat.py / api/rag.py)
Python 无状态(D-D): history/trace_id 由 Java 传入只消费; done 回显 trace_id;
      turns/close/累计 token 归 Java Redis(Python 不建 close/turns 端点)。
"""
import json
import logging
import os

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.chat import verify_internal_token
from core.rag import assistant as rag_assistant
from models.rag_assistant import RagAssistantAskRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag/assistant", tags=["RAG Assistant"])


def _sse(event: str, data: dict) -> str:
    """SSE 事件行(snake_case 数据, Java 中继 camel 化)"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _run_once(req: RagAssistantAskRequest) -> dict:
    """非流式单轮: 消费 pipeline_events → done 数据 + stages 摘要(intent/rewrite/rerank)。

    复用引擎事件序列, 无重复编排逻辑; request=None(非流式不做断连检测)。
    """
    stages: dict = {}
    done: dict | None = None
    async for ev in rag_assistant.pipeline_events(
        req.question, history=req.history, current_project=req.current_project,
        trace_id=req.trace_id, top_k=req.top_k, request=None,
    ):
        name, data = ev["event"], ev["data"]
        if name == "intent":
            stages["intent"] = {
                "anchor": data["anchor"], "category": data["category"],
                "switch_detected": data["switch_detected"], "ambiguous": data["ambiguous"],
            }
        elif name == "rewrite":
            stages["rewrite"] = {"original_question": data["original_question"],
                                 "rewritten_query": data["rewritten_query"]}
        elif name == "rerank":
            stages["rerank"] = data["blocks"]
        elif name == "done":
            done = data
    if done is None:
        raise RuntimeError("pipeline_events 未产出 done 事件")
    done["stages"] = stages
    return done


@router.post("/ask")
async def ask(request: Request, req: RagAssistantAskRequest,
              x_internal_token: str = Header(None)):
    """发起问答: stream=true → SSE 流式; 否则非流式(done + stages 摘要)。

    事件时序(冻结, 无 permission): intent → (clarify|switch) → rewrite → rerank
                                    → (boundary|token*) → done
    """
    verify_internal_token(x_internal_token)
    if req.stream:
        return _ask_stream(request, req)
    try:
        return await _run_once(req)
    except Exception as e:
        logger.error("RAG assistant ask(非流式) 异常: %s", e)
        raise HTTPException(status_code=500, detail="rag assistant ask failed")


def _ask_stream(request: Request, req: RagAssistantAskRequest) -> StreamingResponse:
    """SSE 流式: pipeline_events 逐事件格式化; request 传引擎做 is_disconnected 断连中止。"""

    async def gen():
        try:
            async for ev in rag_assistant.pipeline_events(
                req.question, history=req.history, current_project=req.current_project,
                trace_id=req.trace_id, top_k=req.top_k, request=request,
            ):
                yield _sse(ev["event"], ev["data"])
        except Exception as e:
            logger.error("RAG assistant ask(SSE) 异常: %s", e)
            yield _sse("error", {"code": "500", "message": "rag assistant ask failed"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@router.get("/guide")
async def guide(x_internal_token: str = Header(None)):
    """开始引导(RAG 定向静态池, 0 token, 非 SSE, 不占冻结时序)。"""
    verify_internal_token(x_internal_token)
    return rag_assistant.guide()


@router.get("/eval/report")
async def eval_report(x_internal_token: str = Header(None)):
    """baseline 报告白盒: 最新聚合(hit@3/质量分/avg 耗时/avg 成本/条数/版本)。无报告 → 404。

    读 scripts/rag/run_eval 落盘的 data/eval/reports/<version>.json(结构不变)。
    """
    verify_internal_token(x_internal_token)
    try:
        from scripts.rag import run_eval  # 延迟导入(run_eval 自处理 sys.path)
        reports = [f for f in run_eval._list_reports() if f.endswith(".json")]
        if not reports:
            raise HTTPException(status_code=404, detail="暂无评估报告")
        with open(os.path.join(run_eval.REPORT_DIR, reports[-1]), encoding="utf-8") as f:
            data = json.load(f)
        agg = data.get("aggregate", {})
        return {
            "version": data.get("version", reports[-1].replace(".json", "")),
            "count": agg.get("count", 0),
            "hit_at_3": agg.get("hit_at_k_avg", 0.0),
            "quality_avg": agg.get("quality_avg", 0.0),
            "avg_latency_ms": agg.get("avg_latency_ms", 0),
            "avg_cost_yuan": agg.get("avg_cost_yuan", 0.0),
            "judged_ratio": agg.get("judged_ratio", 0.0),
            "precision_at_3": agg.get("precision_at_k_avg", 0.0),
            "quoted_valid_ratio": agg.get("quoted_valid_ratio", 0.0),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("RAG assistant eval report 异常: %s", e)
        raise HTTPException(status_code=500, detail="rag assistant eval report failed")
