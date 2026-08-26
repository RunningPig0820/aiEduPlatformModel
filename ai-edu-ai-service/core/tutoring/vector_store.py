"""
向量服务核心模块 - dashscope embedding + COS 向量桶(CosVectorsClient)put/query

本期唯一业务用途 = 题型动态聚集(把散题型名归一成 canonical)。多索引 + vector_type
必填路由: 本期唯一合法值 "topic", question/rag 为配置占位(后续加索引零代码改动)。

- embed 独立封装, 不塞进 LLMFactory(gateway 全是 BaseChatModel 对话, embedding 语义不同)
- 失败语义 = 错误冒泡(与 question-understand 的"吞异常降级空结果"相反):
  端点异常返回 HTTP 错误码, Java 桥侧降级(回退字符规则 + 原样落库, 不阻塞主链路)

对齐: openspec/changes/question-type-mastery-python/design.md D1~D5 + api.md
spike 实测(2026-08-18): 768 维对齐 / query 返回字段 vectors / ReturnMetaData(大写 M) /
put 后 ~10s 异步生效 / cosine distance 越小越相似
"""
import json
import logging
from typing import Dict, Any, List, Optional

from openai import OpenAI

from config.settings import settings

logger = logging.getLogger(__name__)

# dashscope embedding 模型 - 复用现成 DASHSCOPE_API_KEY(text-embedding-v3, 百炼默认可用)
_EMBEDDING_MODEL = "text-embedding-v3"
# 显式 768 维(模型默认 1024, 必须与索引维度一致; 索引建好不可改, 见 design D2)
_EMBEDDING_DIMENSIONS = 768
_DASHSCOPE_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# CosVectorsClient 单例懒加载: 避免导入即初始化, 未配齐 COS_* 时 endpoints 仍可加载
_client: Optional[Any] = None

# CosS3Client(普通桶) 单例懒加载: "查看原文"/源文件读写(U4 + upload_cos.py)
_s3_client: Optional[Any] = None


def _get_cos_client() -> Any:
    """CosVectorsClient 单例懒加载。

    仅当 COS_VECTORS_* 配齐(SECRET_ID/KEY/BUCKET 非空)才初始化; 否则抛 RuntimeError,
    由端点层透传为 500(COS 读写失败), Java 桥降级。
    """
    global _client
    if _client is not None:
        return _client

    if not (settings.COS_VECTORS_SECRET_ID and settings.COS_VECTORS_SECRET_KEY):
        raise RuntimeError("COS_VECTORS_* 未配置完整, 无法初始化 CosVectorsClient")

    from qcloud_cos import CosConfig, CosVectorsClient

    _client = CosVectorsClient(CosConfig(
        Region=settings.COS_VECTORS_REGION,
        SecretId=settings.COS_VECTORS_SECRET_ID,
        SecretKey=settings.COS_VECTORS_SECRET_KEY,
    ))
    logger.info("CosVectorsClient 初始化: region=%s bucket=%s indexes=%s",
                settings.COS_VECTORS_REGION, settings.COS_VECTORS_BUCKET, settings.COS_VECTORS_INDEXES)
    return _client


def get_normal_cos_client() -> Any:
    """COS 普通桶(ai-edu-1318177119) CosS3Client 单例懒加载——"查看原文"读源文件(U4)。

    与 CosVectorsClient(向量桶, role mode 不收普通对象)不同: 普通桶支持 get_object/put_object
    (put 由 upload_cos.py 上传, get 由 /api/rag/source 读取)。凭据复用 COS_VECTORS_*。
    """
    global _s3_client
    if _s3_client is not None:
        return _s3_client
    if not (settings.COS_VECTORS_SECRET_ID and settings.COS_VECTORS_SECRET_KEY):
        raise RuntimeError("COS_VECTORS_* 未配置完整, 无法初始化 CosS3Client")

    from qcloud_cos import CosConfig, CosS3Client

    _s3_client = CosS3Client(CosConfig(
        Region=settings.COS_OBJ_REGION,
        SecretId=settings.COS_VECTORS_SECRET_ID,
        SecretKey=settings.COS_VECTORS_SECRET_KEY,
    ))
    logger.info("CosS3Client(普通桶) 初始化: region=%s bucket=%s",
                settings.COS_OBJ_REGION, settings.COS_OBJ_BUCKET)
    return _s3_client


def embed(text: str) -> List[float]:
    """文本 → dashscope embedding 向量(768 维)。

    复用现成 DASHSCOPE_API_KEY + dashscope OpenAI 兼容 base(与 factory.py bailian 同一 base)。
    失败抛异常(embedding 失败 tag), 由端点层透传为 500。
    """
    client = OpenAI(api_key=settings.DASHSCOPE_API_KEY, base_url=_DASHSCOPE_BASE)
    resp = client.embeddings.create(
        model=_EMBEDDING_MODEL,
        input=text,
        dimensions=_EMBEDDING_DIMENSIONS,
    )
    vector = resp.data[0].embedding
    if len(vector) != _EMBEDDING_DIMENSIONS:
        logger.error("embedding 维度异常: 期望 %d, 实际 %d", _EMBEDDING_DIMENSIONS, len(vector))
        raise RuntimeError(f"embedding dimension mismatch: {len(vector)} != {_EMBEDDING_DIMENSIONS}")
    return vector


def _resolve_bucket_index(vector_type: str) -> tuple:
    """vector_type(逻辑名) → (bucket, index)。rag* 走独立 RAG 桶, 其余走默认桶。未知 → ValueError。

    桶隔离: topic(题型聚集) 在 question-bank-1318177119, rag/rag-full/rag-slice(双池) 在 rag-1318177119,
    互不影响(重建 rag-slice 不碰 topic 生产查询)。
    """
    index = settings.COS_VECTORS_INDEXES.get(vector_type)
    if not index:
        raise ValueError(f"unknown vector_type: {vector_type!r}, 合法值: {list(settings.COS_VECTORS_INDEXES.keys())}")
    if vector_type.startswith("rag"):
        bucket = settings.COS_VECTORS_RAG_BUCKET
        if not bucket:
            raise RuntimeError("COS_VECTORS_RAG_BUCKET 未配置, 无法路由 rag 向量")
    else:
        bucket = settings.COS_VECTORS_BUCKET
    return bucket, index


def put_vector(key: str, text: str, vector_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """embed → put_vectors 写入对应索引(按 vector_type 路由桶)。

    key 相同 upsert 覆盖。write 后 ~10s 异步生效(CS 向量索引), 立即 query 可能 miss。
    """
    bucket, index = _resolve_bucket_index(vector_type)
    vector = embed(text)
    client = _get_cos_client()
    try:
        client.put_vectors(
            Bucket=bucket,
            Index=index,
            Vectors=[{
                "key": key,
                "data": {"float32": vector},
                "metadata": metadata or {},
            }],
        )
    except Exception as e:
        logger.error("vector COS put 失败: type=%s bucket=%s index=%s key=%s: %s",
                     vector_type, bucket, index, key, e)
        raise
    logger.info("vector put: type=%s bucket=%s index=%s key=%s dim=%d",
                vector_type, bucket, index, key, len(vector))


def query_vector(text: str, top_k: int, vector_type: str,
                 filter_: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """embed → query_vectors 查最近邻 Top-K(按 vector_type 路由桶)。

    filter_(1.13 多模块): COS 条件筛选(如 {"module": {"$eq": "ai-tutoring"}} 或
    {"$and": [...]})——在向量层过滤, 不让其他模块/类别的相似向量挤占 top-k。
    返回命中列表(COS data["vectors"], 每项 {key, metadata, distance}), 按 distance 升序。
    """
    bucket, index = _resolve_bucket_index(vector_type)
    vector = embed(text)
    client = _get_cos_client()
    kw = {"ReturnMetaData": True, "ReturnDistance": True}
    if filter_:
        kw["Filter"] = filter_
    try:
        _, data = client.query_vectors(
            Bucket=bucket,
            Index=index,
            QueryVector={"float32": vector},
            TopK=top_k,
            **kw,
        )
    except Exception as e:
        logger.error("vector COS query 失败: type=%s bucket=%s index=%s top_k=%d: %s",
                     vector_type, bucket, index, top_k, e)
        raise
    hits = data.get("vectors", [])
    logger.info("vector query: type=%s bucket=%s index=%s top_k=%d hits=%d",
                vector_type, bucket, index, top_k, len(hits))
    return hits