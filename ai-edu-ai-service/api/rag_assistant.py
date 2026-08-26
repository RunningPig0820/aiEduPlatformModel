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
import threading

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from api.chat import verify_internal_token
from core.rag import assistant as rag_assistant
from models.rag_assistant import RagAssistantAskRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag/assistant", tags=["RAG Assistant"])

# ---- 评测运行状态(线程安全)----
# 现场演示"重新评测": POST /eval/run 后台线程真实跑一轮, 全局标志防重复触发。
# 异步模型(立即 200, 前端轮询 GET /eval/report.running), 不阻塞 HTTP。
_eval_running = False
_eval_lock = threading.Lock()


def _eval_in_progress() -> bool:
    """线程安全读 running 标志。"""
    with _eval_lock:
        return _eval_running


def _set_eval_running(flag: bool) -> None:
    global _eval_running
    with _eval_lock:
        _eval_running = flag


def _start_eval_async() -> bool:
    """尝试启动一轮后台评测; 已有一轮在跑 → False(幂等, 不重复触发)。"""
    with _eval_lock:
        global _eval_running
        if _eval_running:
            return False
        _eval_running = True

    def _run():
        try:
            from scripts.rag import run_eval
            run_eval.run_evaluation()
        except Exception as e:
            logger.error("后台评测异常: %s", e)
        finally:
            _set_eval_running(False)

    threading.Thread(target=_run, daemon=True).start()
    return True


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
async def guide(current_project: str | None = None, x_internal_token: str = Header(None)):
    """开始引导(M6 模块底座池, 0 token, 非 SSE, 不占冻结时序)。

    current_project(可选 query, 后端 ?current_project= 透传): 每功能引导问题不同,
    进页面/切换功能以当前功能为准; 缺省/未知 → FALLBACK_MODULE(ai-tutoring)。
    """
    verify_internal_token(x_internal_token)
    return rag_assistant.guide(current_project)


@router.get("/eval/report")
async def eval_report(x_internal_token: str = Header(None)):
    """baseline 报告白盒: 最新聚合(hit@3/质量分/avg 耗时/avg 成本/条数/版本) + 运行态。

    读 scripts/rag/run_eval 落盘的 data/eval/reports/<version>.json(结构不变)。
    现场演示字段: evaluated_at(最近运行时间=报告文件 mtime) / running(评测进行中)。
    """
    verify_internal_token(x_internal_token)
    try:
        from scripts.rag import run_eval  # 延迟导入(run_eval 自处理 sys.path)
        reports = [f for f in run_eval._list_reports() if f.endswith(".json")]
        if not reports:
            raise HTTPException(status_code=404, detail="暂无评估报告")
        # 最新报告按 mtime 选(版本=语料 sha1 前缀, 与生成时间无关, 不能靠文件名排序取末位)
        report_name = max(reports, key=lambda f: os.path.getmtime(
            os.path.join(run_eval.REPORT_DIR, f)))
        report_path = os.path.join(run_eval.REPORT_DIR, report_name)
        with open(report_path, encoding="utf-8") as f:
            data = json.load(f)
        agg = data.get("aggregate", {})
        # evaluated_at: 最近一次运行时间 = 报告文件 mtime(ISO 本地时间)
        import datetime
        evaluated_at = datetime.datetime.fromtimestamp(
            os.path.getmtime(report_path)).isoformat(timespec="seconds")
        return {
            "version": data.get("version", report_name.replace(".json", "")),
            "count": agg.get("count", 0),
            "hit_at_3": agg.get("hit_at_k_avg", 0.0),
            "quality_avg": agg.get("quality_avg", 0.0),
            "avg_latency_ms": agg.get("avg_latency_ms", 0),
            "avg_cost_yuan": agg.get("avg_cost_yuan", 0.0),
            "judged_ratio": agg.get("judged_ratio", 0.0),
            "precision_at_3": agg.get("precision_at_k_avg", 0.0),
            "quoted_valid_ratio": agg.get("quoted_valid_ratio", 0.0),
            # 现场演示字段(Java 代理已就绪映射: evaluatedAt/hitCases/avgTokens/totalCostYuan/running)
            "evaluated_at": evaluated_at,
            "hit_cases": agg.get("hit_cases", 0),
            "avg_tokens": agg.get("avg_tokens", 0),
            "total_cost_yuan": agg.get("total_cost_yuan", 0.0),
            "running": _eval_in_progress(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("RAG assistant eval report 异常: %s", e)
        raise HTTPException(status_code=500, detail="rag assistant eval report failed")


@router.post("/eval/run")
async def eval_run(x_internal_token: str = Header(None)):
    """触发重新评测(异步, 现场演示用): 后台线程真实跑一轮, 立即返回 200。

    - 首次触发 → {"running": true, "already_running": false}, 后台跑几分钟
    - 已有一轮在跑 → {"running": true, "already_running": true}(幂等, 前端当正常状态)
    - 前端轮询 GET /eval/report 的 running=false 后刷新(Java 代理已就绪)
    """
    verify_internal_token(x_internal_token)
    started = _start_eval_async()
    return {"running": True, "already_running": not started}
