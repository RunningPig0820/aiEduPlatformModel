"""
RAG 查询 API - 前端/后端调 `POST /api/tutoring/rag/query`

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.6C 查询 API 契约
鉴权: x-internal-token(同 api/vector.py / api/chat.py)
健壮性(1.6C 降级语义, 按序):
  1. COS 向量挂了   → 降级纯 BM25(references 仍返回)
  2. doubao 挂了    → 降级返回召回块清单(references 当答案, 不空答)
  3. 置信度过低     → 拒答"语料未覆盖", 不编造
  4. 所有降级路径 response 结构不变(前端只按同一结构渲染)
"""
import logging

from fastapi import APIRouter, Header, HTTPException

from api.chat import verify_internal_token
from core.rag import query as rag_core
from models.rag import (
    RAGQueryRequest,
    RAGQueryResponse,
    RAGReference,
    RAGIntent,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutoring/rag", tags=["Tutoring"])


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
