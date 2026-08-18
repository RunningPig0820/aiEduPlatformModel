"""
向量服务数据模型 - Java 后端与 Python 向量服务的契约层

支撑后端题型动态聚集(把散题型名归并成 canonical)。纯数据定义,无业务逻辑。
独立于 models/tutoring.py(decide/generate/question-understand 零改动)。

对齐文档: openspec/changes/question-type-mastery-python/api.md + design.md(D1/D3)
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# ============ put 存向量 ============


class VectorPutRequest(BaseModel):
    """向量写入请求 - Java 调 `POST /api/tutoring/vector/put`

    vector_type 必填: 索引路由键, 每次由后端显式确定(本期唯一合法值 "topic")。
    """
    key: str = Field(..., description="向量业务 ID(key 相同覆盖 upsert)")
    text: str = Field(..., description="要向量化的文本(本期为题型名; 题目文本不落库)")
    vector_type: str = Field(..., description="索引路由键, 必填, 本期唯一合法值 'topic'")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="透传存进向量桶(student_id/topic_label/canonical_label/timestamp), Python 不改写")


class VectorPutResponse(BaseModel):
    """向量写入响应"""
    ok: bool = Field(..., description="是否成功")
    key: str = Field(..., description="写入的向量 key")


# ============ query 查最近邻 ============


class VectorQueryRequest(BaseModel):
    """向量查询请求 - Java 调 `POST /api/tutoring/vector/query`

    vector_type 必填: 查询哪个索引, 每次由后端显式确定(本期唯一合法值 "topic")。
    """
    text: str = Field(..., description="要向量化的查询文本")
    top_k: int = Field(default=5, ge=1, le=100, description="返回最近邻条数")
    vector_type: str = Field(..., description="索引路由键, 必填, 本期唯一合法值 'topic'")


class VectorHit(BaseModel):
    """最近邻命中项 - 响应字段对齐 COS query_vectors 返回"""
    key: str = Field(..., description="向量 key")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="该向量存入时的 metadata")
    distance: float = Field(..., description="余弦距离, 越小越相似(self 命中 ≈ 0)")


class VectorQueryResponse(BaseModel):
    """向量查询响应 - 字段名 vectors 对齐 COS 返回(非 hits)"""
    vectors: List[VectorHit] = Field(default_factory=list, description="最近邻列表, 按 distance 升序; 无近邻返回空数组")