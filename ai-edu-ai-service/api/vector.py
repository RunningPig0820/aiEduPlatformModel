"""
向量服务 API 端点 - Java↔Python 内部调用(需 x-internal-token)

- POST /api/tutoring/vector/put    存向量(embed → CosVectorsClient 写入, key 相同 upsert)
- POST /api/tutoring/vector/query  查最近邻(embed → CosVectorsClient 查询 → Top-K)

对齐: openspec/changes/question-type-mastery-python/api.md(snake_case, vector_type 必填)
失败语义 = 错误冒泡(design D5): 异常返回 HTTP 错误码, Java 桥侧降级(回退字符规则 + 原样落库)。
不同于 question-understand 的"吞异常降级空结果"——向量是基础设施, 让 Java 感知失败。
"""
import logging

from fastapi import APIRouter, Header, HTTPException

from api.chat import verify_internal_token
from core.tutoring import vector_store
from models.vector import (
    VectorPutRequest,
    VectorPutResponse,
    VectorQueryRequest,
    VectorQueryResponse,
    VectorHit,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutoring/vector", tags=["Tutoring"])


@router.post("/put", response_model=VectorPutResponse)
async def vector_put(
    request: VectorPutRequest,
    x_internal_token: str = Header(None),
):
    """存向量(同步 JSON): text → embedding(768 维) → 写入 vector_type 对应索引。key 相同 upsert。"""
    verify_internal_token(x_internal_token)
    try:
        vector_store.put_vector(
            key=request.key,
            text=request.text,
            vector_type=request.vector_type,
            metadata=request.metadata,
        )
        return VectorPutResponse(ok=True, key=request.key)
    except ValueError as e:
        # 未知 vector_type → 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("vector put 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="vector put failed")


@router.post("/query", response_model=VectorQueryResponse)
async def vector_query(
    request: VectorQueryRequest,
    x_internal_token: str = Header(None),
):
    """查最近邻(同步 JSON): text → embedding(768 维) → 查 vector_type 对应索引 Top-K, 按 distance 升序。"""
    verify_internal_token(x_internal_token)
    try:
        hits = vector_store.query_vector(
            text=request.text,
            top_k=request.top_k,
            vector_type=request.vector_type,
        )
        return VectorQueryResponse(
            vectors=[
                VectorHit(
                    key=h["key"],
                    metadata=h.get("metadata", {}),
                    distance=h.get("distance", 0.0),
                )
                for h in hits
            ]
        )
    except ValueError as e:
        # 未知 vector_type → 400
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("vector query 端点异常: %s", e)
        raise HTTPException(status_code=500, detail="vector query failed")