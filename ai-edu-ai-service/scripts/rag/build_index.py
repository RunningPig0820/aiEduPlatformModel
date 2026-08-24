"""
1.6 索引构建 - 纯 COS 向量桶写入(rag-1318177119/rag-index)

每块 embedding 文本 = summary + "\n" + text(summary 引导命中, text 供细节)。
metadata 含 tags + version + doc_type(summary 一块; text 不进 metadata, 20KB 限制, 检索后按 key 反查 jsonl)。

用法: cd ai-edu-ai-service && python scripts/rag/build_index.py [--clear]
输入: scripts/rag/data/rag_slices.jsonl
输出: rag-1318177119/rag-index 向量(234 块); 语料 jsonl 留本地(向量桶 role mode 不收普通对象)

--clear: list_vectors 枚举全部 key → delete_vectors 清空 → 重写(幂等重建, 对齐 project-intro-rag)。
对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.6A + openspec/changes/project-intro-rag/
"""
import argparse
import hashlib
import json
import logging
import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from config.settings import settings
from core.tutoring.vector_store import _get_cos_client, _resolve_bucket_index, embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl")
VECTOR_TYPE = "rag"
BATCH_PUT = 20        # put_vectors 单批条数(服务端上限约束)
BATCH_DELETE = 100    # delete_vectors 单批条数
LIST_PAGE = 200       # list_vectors 分页大小
WAIT_SECONDS = 10     # put 后异步生效等待(spike 实测 ~10s)


def make_key(file_: str, anchor: str, idx: int) -> str:
    """块唯一 key: ai-tutoring/{file}/{anchor}#{chunk_idx}。同 key upsert, 不带版本。"""
    return f"ai-tutoring/{file_}/{anchor}#{idx}"


def make_version(blocks: list) -> str:
    """version = YYYY-MM-DD-<语料 sha1[:6]>; 语料变 → 版本变 → 可回退, 走 metadata 不走索引名。"""
    raw = "".join(b["text"] for b in blocks).encode("utf-8")
    sha = hashlib.sha1(raw).hexdigest()[:6]
    today = time.strftime("%Y-%m-%d")
    return f"{today}-{sha}"


def list_all_keys(client, bucket: str, index: str) -> list:
    """list_vectors 分页枚举全部 key(仅需 key, 不带数据/metadata)。"""
    keys, token = [], None
    while True:
        kw = {"MaxResults": LIST_PAGE, "NextToken": token} if token else {"MaxResults": LIST_PAGE}
        _, data = client.list_vectors(Bucket=bucket, Index=index, ReturnData=False, ReturnMetaData=False, **kw)
        keys.extend(v["key"] for v in data.get("vectors", []))
        token = data.get("nextToken")
        if not token:
            break
    return keys


def clear_index(client, bucket: str, index: str) -> None:
    """--clear 幂等清空: list → 分批 delete(空索引也兼容, list 为空直接跳过)。"""
    keys = list_all_keys(client, bucket, index)
    logger.info("清空 rag-index: 现有 %d 条", len(keys))
    for i in range(0, len(keys), BATCH_DELETE):
        client.delete_vectors(Bucket=bucket, Index=index, Keys=keys[i:i + BATCH_DELETE])
    if keys:
        logger.info("已删除 %d 条, 等 %ds 生效...", len(keys), WAIT_SECONDS)
        time.sleep(WAIT_SECONDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clear", action="store_true", help="清空 rag-index 后重写(幂等重建)")
    args = ap.parse_args()

    bucket, index = _resolve_bucket_index(VECTOR_TYPE)
    logger.info("目标: bucket=%s index=%s (from %s)", bucket, index, settings.COS_VECTORS_RAG_BUCKET)

    client = _get_cos_client()
    # 校验 rag-index 已建(控制台建, 脚本不建索引)。缺失 → 报错提示先建。
    try:
        client.get_index(Bucket=bucket, Index=index)
    except Exception as e:
        logger.error("get_index 失败: bucket=%s index=%s(需在控制台先建 768/float32/cosine): %s",
                     bucket, index, e)
        sys.exit(1)

    if args.clear:
        clear_index(client, bucket, index)

    with open(DATA, encoding="utf-8") as f:
        blocks = [json.loads(line) for line in f if line.strip()]
    version = make_version(blocks)
    logger.info("读 %d 块, version=%s, 开始 embedding(dashscope 768d)...", len(blocks), version)

    # chunk_idx: 同 (file, anchor) 内序号(段落拆块/同锚点多块防 key 冲突)
    counters = {}
    payloads = []
    for b in blocks:
        t = b["tags"]
        group = (t["file"], t["anchor"])
        idx = counters.get(group, 0)
        counters[group] = idx + 1
        key = make_key(t["file"], t["anchor"], idx)
        text = (b["summary"] + "\n" + b["text"])
        metadata = {
            "version": version,
            "doc_type": "ai-tutoring",
            "source": t["source"],
            "authority": t["authority"],
            "section": t["section"],
            "file": t["file"],
            "file_path": t.get("file_path", ""),
            "anchor": t["anchor"],
            "summary": b["summary"],
        }
        payloads.append({"key": key, "data": {"float32": embed(text)}, "metadata": metadata})

    for i in range(0, len(payloads), BATCH_PUT):
        client.put_vectors(Bucket=bucket, Index=index, Vectors=payloads[i:i + BATCH_PUT])
        logger.info("put_vectors 批次 %d/%d", i // BATCH_PUT + 1, (len(payloads) - 1) // BATCH_PUT + 1)

    logger.info("已写入 %d 块, 等 %ds 异步生效...", len(payloads), WAIT_SECONDS)
    time.sleep(WAIT_SECONDS)

    # 语料 jsonl 留本地(version 对应): BM25/反查运行时从本地读。
    # 【不传 COS 普通对象】——向量桶是 role mode, put_object 被拒(AccessDenied), 设计已调整。
    logger.info("语料副本留本地: %s (version=%s, 向量桶 role mode 不收普通对象)", DATA, version)


if __name__ == "__main__":
    main()
