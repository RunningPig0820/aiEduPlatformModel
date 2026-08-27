"""
阶段3 索引构建 - 纯 COS 向量桶写入(rag-1318177119/rag-full|rag-slice, 双池)

每块 embedding 文本 = summary + "\n" + text(summary 引导命中, text 供细节)。
双向量(task #78, 2026-08-26): **切片池(slice)每块写两个 key**, 同索引 rag-slice, key 后缀 role 区分:
  - `-c` = embed(summary+text) 内容路
  - `-q` = embed(summary)      summary/问题路(query 是问题形态, 匹配"问题"侧更准)
  全量池(full)整篇文档非问答结构, 保持单向量, **条件式 embed**(2026-08-27 改):
  - summary+全文 ≤ FULL_EMBED_MAX_CHARS(5000 字符) → embed(summary+全文) 保全文(完善文档 1.0 主答案/代码 0.8)
  - 超限大文件(语雀 10~12K 字符) → 只 embed(summary) 摘要向量, 防整篇 text 超 8192 token 被 dashscope 静默截断。
  控制台无需新建索引; 不加 metadata(10 字段上限)。
metadata 10 字段(≤COS 向量索引上限): version/module/category/source/authority/section/file/file_path/anchor/summary
(text 不进 metadata, 20KB 限制, 检索后按 key 反查 jsonl)。

用法: cd ai-edu-ai-service && python scripts/rag/build_index.py --pool full|slice [--clear]
输入: --pool full  → scripts/rag/data/rag_slices_full.jsonl(23 块整篇)
      --pool slice → scripts/rag/data/rag_slices.jsonl(294 块切片)
输出: rag-1318177119 / rag-full(全量池) 或 rag-slice(切片池); 语料 jsonl 留本地(BM25/反查)

--clear: 该池 list_vectors 枚举全部 key → delete_vectors 清空 → 重写(幂等, 各池各清)。
对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.13 B1-B2
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

# 池 → (vector_type, jsonl 文件名)。vector_type = 池前缀(rag-full/rag-slice), 同 key 规则。
POOLS = {
    "full":  {"vector_type": "rag-full",  "data": "rag_slices_full.jsonl"},
    "slice": {"vector_type": "rag-slice", "data": "rag_slices.jsonl"},
}
BATCH_PUT = 20        # put_vectors 单批条数(服务端上限约束)
BATCH_DELETE = 100    # delete_vectors 单批条数
LIST_PAGE = 200       # list_vectors 分页大小
WAIT_SECONDS = 10     # put 后异步生效等待(spike 实测 ~10s)
FULL_EMBED_MAX_CHARS = 5000  # 全量池条件式阈值: ≤ 此字符 embed(summary+全文), 超限只 embed(summary) 防 8192 token 截断


def make_key(vector_type: str, file_: str, anchor: str, idx: int) -> str:
    """块唯一 key: {池前缀}/{file}/{anchor}#{chunk_idx}, 池前缀防两池 (file,anchor) 冲突。"""
    return f"{vector_type}/{file_}/{anchor}#{idx}"


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
    logger.info("清空 %s: 现有 %d 条", index, len(keys))
    for i in range(0, len(keys), BATCH_DELETE):
        client.delete_vectors(Bucket=bucket, Index=index, Keys=keys[i:i + BATCH_DELETE])
    if keys:
        logger.info("已删除 %d 条, 等 %ds 生效...", len(keys), WAIT_SECONDS)
        time.sleep(WAIT_SECONDS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", choices=list(POOLS), required=True,
                    help="full=全量池(rag-full), slice=切片池(rag-slice)")
    ap.add_argument("--clear", action="store_true", help="清空该池索引后重写(幂等重建)")
    args = ap.parse_args()

    cfg = POOLS[args.pool]
    vector_type = cfg["vector_type"]
    data = os.path.join(os.path.dirname(__file__), "data", cfg["data"])

    bucket, index = _resolve_bucket_index(vector_type)
    logger.info("目标: bucket=%s index=%s (pool=%s, 双池)", bucket, index, args.pool)

    client = _get_cos_client()
    # 校验索引已建(控制台建, 脚本不建索引)。缺失 → 报错提示先建。
    try:
        client.get_index(Bucket=bucket, Index=index)
    except Exception as e:
        logger.error("get_index 失败: bucket=%s index=%s(需在控制台先建 768/float32/cosine): %s",
                     bucket, index, e)
        sys.exit(1)

    if args.clear:
        clear_index(client, bucket, index)

    with open(data, encoding="utf-8") as f:
        blocks = [json.loads(line) for line in f if line.strip()]
    version = make_version(blocks)
    logger.info("读 %d 块(pool=%s), version=%s, 开始 embedding(dashscope 768d)...",
                len(blocks), args.pool, version)

    # chunk_idx: 同 (file, anchor) 内序号(段落拆块/同锚点多块防 key 冲突)
    counters = {}
    payloads = []
    for b in blocks:
        t = b["tags"]
        group = (t["file"], t["anchor"])
        idx = counters.get(group, 0)
        counters[group] = idx + 1
        key = make_key(vector_type, t["file"], t["anchor"], idx)
        # 注意: COS 向量索引 metadata 单条 ≤10 entries(实测), 现 10 字段恰好上限。
        # doc_type 与 module 同值冗余已去掉(2026-08-26); 新增字段需先删一个。
        metadata = {
            "version": version,
            # 模块标识(多模块同索引区分, 与 slice_corpus._tags 闭集一致: ai-tutoring/knowledge-graph/...)
            "module": t.get("module", "ai-tutoring"),
            "category": t.get("category", ""),   # 9类闭集标签(项目介绍/操作流程/...); 检索按类别筛选
            "source": t["source"],
            "authority": t["authority"],
            "section": t["section"],
            "file": t["file"],
            "file_path": t.get("file_path", ""),
            "anchor": t["anchor"],
            "summary": b["summary"],
        }
        if args.pool == "slice":
            # 双向量(task #78): 每块写两个 key, 同索引 rag-slice, key 后缀 role 区分(不加 metadata)
            #   -c 内容路 embed(summary+text), -q summary/问题路 embed(summary)
            content = {"key": key + "-c",
                       "data": {"float32": embed(b["summary"] + "\n" + b["text"])},
                       "metadata": metadata}
            question = {"key": key + "-q",
                        "data": {"float32": embed(b["summary"])},
                        "metadata": metadata}
            payloads.extend([content, question])
        else:
            # 全量池(整篇文档, 非问答结构)单向量 = 条件式(2026-08-27 改)
            #   ≤ FULL_EMBED_MAX_CHARS → embed(summary+全文): 完善文档 1.0 主答案/代码 0.8 全文进向量可检索
            #   >  FULL_EMBED_MAX_CHARS → embed(summary): 大语雀(10~12K 字符)超 8192 token 防静默截断, 摘要作文档级粗召回
            # text 仍留 jsonl 供 BM25/反查/查看原文, 不进向量。
            full_text = b["summary"] + "\n" + b["text"]
            data = embed(full_text) if len(full_text) <= FULL_EMBED_MAX_CHARS else embed(b["summary"])
            payloads.append({"key": key, "data": {"float32": data}, "metadata": metadata})

    for i in range(0, len(payloads), BATCH_PUT):
        client.put_vectors(Bucket=bucket, Index=index, Vectors=payloads[i:i + BATCH_PUT])
        logger.info("put_vectors 批次 %d/%d", i // BATCH_PUT + 1, (len(payloads) - 1) // BATCH_PUT + 1)

    logger.info("已写入 %d 块, 等 %ds 异步生效...", len(payloads), WAIT_SECONDS)
    time.sleep(WAIT_SECONDS)

    # 语料 jsonl 留本地(version 对应): BM25/反查运行时从本地读。
    # 【不传 COS 普通对象】——向量桶是 role mode, put_object 被拒(AccessDenied), 设计已调整。
    logger.info("语料副本留本地: %s (version=%s, 向量桶 role mode 不收普通对象)", data, version)


if __name__ == "__main__":
    main()
