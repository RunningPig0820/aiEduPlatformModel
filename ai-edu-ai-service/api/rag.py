"""
RAG API - 前端/后端调:
  - `POST /api/tutoring/rag/query`   RAG 问答(1.6C 契约)
  - `POST /api/rag/eval/run`         触发评测(6.1, 离线工具, 同步执行 ~30s)
  - `GET  /api/rag/eval/report`      查询最新报告 + 版本对比(6.2)

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.6C + 6
鉴权: x-internal-token(同 api/vector.py / api/chat.py)
健壮性(1.6C 降级语义, 按序):
  1. COS 向量挂了   → 降级纯 BM25(references 仍返回)
  2. doubao 挂了    → 降级返回召回块清单(references 当答案, 不空答)
  3. 置信度过低     → 拒答"语料未覆盖", 不编造
  4. 所有降级路径 response 结构不变(前端只按同一结构渲染)
"""
import logging
import os

from fastapi import APIRouter, Header, HTTPException
from fastapi.concurrency import run_in_threadpool

from api.chat import verify_internal_token
from core.rag import query as rag_core
from models.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGReference,
    RAGIntent,
    RAGEvalRunResponse,
    RAGEvalReportResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutoring/rag", tags=["Tutoring"])
EVAL_ROUTER = APIRouter(prefix="/api/rag/eval", tags=["RAG Eval"])

# run_eval 在 scripts/rag/(评测执行), API 侧按需延迟导入(避免 import 链过早初始化)
EVAL_RUN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "scripts", "rag", "run_eval.py")


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    x_internal_token: str = Header(None),
):
    """RAG 问答: 意图 → 双路召回 → 编排 → doubao 生成。降级语义见模块 docstring。"""
    verify_internal_token(x_internal_token)

    # --- 1.6C 降级语义: COS 向量挂了 → 降级纯 BM25(需绕开 rag_query 的整链路) ---
    try:
        blocks = rag_core._load_blocks()
        strategy = rag_core.classify(request.question)

        # 向量路失败冒泡 → 捕获降级纯 BM25(构造空向量结果)
        try:
            vec = rag_core.retrieve_vector(request.question)
        except Exception as e:
            logger.warning("RAG 向量路失败, 降级纯 BM25: %s", e)
            vec = {"hits": [], "confidence": 0.0}

        bm = rag_core.retrieve_bm25(request.question, blocks)
        hits = rag_core.orchestrate(request.question, blocks, vec, bm, strategy,
                                    top_k=request.top_k)

        references = [
            RAGReference(**{k: h[k] for k in ("file", "file_path", "anchor", "authority", "summary")})
            for h in hits
        ]
        intent = RAGIntent(locked_sections=strategy["locked_sections"],
                           strategy=strategy["strategy"])

        # --- 降级语义 3: 无命中 → 拒答不编造 ---
        if not hits:
            return RAGQueryResponse(
                answer="该问题语料未覆盖，建议问项目相关话题",
                references=[],
                intent=intent,
                version=rag_core._current_version(blocks),
            )

        # --- 降级语义 2: doubao 挂了 → references 当答案, 不空答 ---
        try:
            answer = rag_core.generate(hits, request.question)
        except Exception as e:
            logger.error("RAG 生成失败(doubao), 降级返回召回块清单: %s", e)
            answer = "生成服务不可用，以下为检索到的语料：\n" + "\n".join(
                f"- [{h['file']}/{h['anchor']}] {h['summary']}" for h in hits
            )

        return RAGQueryResponse(
            answer=answer,
            references=references,
            intent=intent,
            version=rag_core._current_version(blocks),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("RAG query 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="rag query failed")


# ============ 6 评测 API(离线工具上线, 6.1/6.2/6.3) ============


@EVAL_ROUTER.post("/run", response_model=RAGEvalRunResponse)
async def eval_run(x_internal_token: str = Header(None)):
    """触发评测(6.1): 跑评测集 → 聚合报告 → 落盘。离线工具, 同步执行(~30s)。"""
    verify_internal_token(x_internal_token)
    try:
        from scripts.rag import run_eval  # 延迟导入(run_eval 自处理 sys.path)
        out = await run_in_threadpool(run_eval.run_evaluation)  # 不阻塞事件循环
        return RAGEvalRunResponse(
            ok=True,
            version=out["version"],
            aggregate=out["aggregate"],
            report_path=out["report_path"],
        )
    except Exception as e:
        logger.error("RAG eval run 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="rag eval run failed")


@EVAL_ROUTER.get("/report", response_model=RAGEvalReportResponse)
async def eval_report(x_internal_token: str = Header(None)):
    """查询评测报告(6.2): 最新聚合 + 历史版本列表(供版本对比)。"""
    verify_internal_token(x_internal_token)
    try:
        from scripts.rag import run_eval
        reports = run_eval._list_reports()
        if not reports:
            return RAGEvalReportResponse(ok=True, has_report=False, reports=[])
        latest = reports[-1]
        import json
        with open(os.path.join(run_eval.REPORT_DIR, latest), encoding="utf-8") as f:
            data = json.load(f)
        return RAGEvalReportResponse(
            ok=True,
            version=data.get("version", latest.replace(".json", "")),
            aggregate=data.get("aggregate", {}),
            reports=reports,
            has_report=True,
        )
    except Exception as e:
        logger.error("RAG eval report 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="rag eval report failed")
