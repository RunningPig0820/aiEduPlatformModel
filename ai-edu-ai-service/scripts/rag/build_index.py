"""
1.6 索引构建 - dashscope embedding + numpy 余弦(本地, 不依赖网络外部服务)

每块 embedding 文本 = summary + text 拼接(summary 引导命中, text 供细节)。
输出本地 npz: 归一化向量矩阵 + 块元数据(文本/tags), 供 rag_query.py 检索。
生产可换 COS 向量桶(接口同 embed, 见 core/tutoring/vector_store.py)。

用法: cd ai-edu-ai-service && python scripts/rag/build_index.py
输入: scripts/rag/data/rag_slices.jsonl
输出: scripts/rag/data/rag_index.npz
"""
import json
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import numpy as np

from core.tutoring.vector_store import embed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl")
OUT = os.path.join(os.path.dirname(__file__), "data", "rag_index.npz")


def main():
    with open(DATA, encoding="utf-8") as f:
        blocks = [json.loads(line) for line in f if line.strip()]
    logger.info("读 %d 块, 开始 embedding(dashscope 768d)...", len(blocks))

    texts, metas = [], []
    for b in blocks:
        # 嵌入文本 = summary(引导命中) + 原文(细节)
        texts.append((b["summary"] + "\n" + b["text"]))
        metas.append({"text": b["text"], "summary": b["summary"], "tags": b["tags"]})

    vecs = [embed(t) for t in texts]
    V = np.array(vecs, dtype=np.float32)
    # 归一化(余弦距离用)
    norms = np.linalg.norm(V, axis=1, keepdims=True)
    V = V / np.where(norms == 0, 1, norms)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez(OUT,
             vectors=V,
             meta=json.dumps(metas, ensure_ascii=False))
    logger.info("索引完成: %d 块, 维度 %d → %s", len(blocks), V.shape[1], OUT)


if __name__ == "__main__":
    main()
