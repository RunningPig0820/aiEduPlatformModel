"""
全量池整篇文档摘要生成 - LLM 推断(doubao, 逐篇)

全量池(rag_slices_full.jsonl)每块是整篇文档(完善文档 8 / 语雀 5 / 代码 10)。
build_index 全量池 embed(summary) 作文档级粗召回(2026-08-27 改, 防大文件超 8192 token 截断),
所以 summary 必须是**文档级摘要**(覆盖全文主题), 不能是旧 jsonl 复用/切片摘要拼接。

本脚本为每份整篇文档**逐篇**生成文档级 summary(2026-08-27 改逐篇: 批量 index 数组 doubao 会
合并成一份摘要, 每篇单独调用才可靠):
- 站在"面试问答检索"角度, 说清"这文档覆盖什么 / 解决什么问题"
- 文档级(40~80 字), 覆盖全文主题, 命中业务实体/动作/场景关键词
- 逐篇调用, 关思考(快) + 20s 超时 + 关重试; 失败该篇留旧摘要可重跑

用法: cd ai-edu-ai-service && python scripts/rag/gen_full_summaries.py
输入: scripts/rag/data/rag_slices_full.jsonl
输出: scripts/rag/data/rag_slices_full.jsonl (summary 字段重写)
"""
import json
import logging
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings
from core.gateway.factory import LLMFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA = os.path.join(os.path.dirname(__file__), "data", "rag_slices_full.jsonl")
CTX = 3000     # 每份文档喂给 LLM 的正文长度(头 3000 字符含小节标题, 足够看覆盖主题)

_SYSTEM = """你是 RAG 文档级摘要器。对给定的**一个**整篇文档，输出文档级 summary：
- 站在"面试问答检索"角度，说清"这文档覆盖什么 / 解决什么问题"
- 覆盖全文主题，40~80 字，能命中业务实体、动作、场景关键词
- 口语、自包含，直接说内容，不要"本文档""该文"这类代词开头
- 只输出 summary 文本本身，不要 JSON 包裹、不要解释"""


def _make_llm():
    return LLMFactory.create(
        "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.0,
        extra_body={"thinking": {"type": "disabled"}},
        request_timeout=20, max_retries=0,
    )


def _gen_one(llm, doc: dict) -> str | None:
    """单篇文档 → 文档级 summary; 失败返回 None(留旧摘要, 可重跑)"""
    prompt = f"文件: {doc['tags']['file']}\n正文:\n{doc['text'][:CTX]}"
    try:
        resp = llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=prompt),
        ])
        s = resp.content.strip().strip('"\'')
        return s if s else None
    except Exception as e:
        logger.warning("文档级摘要生成失败(%s): %s", doc["tags"]["file"], e)
        return None


def main():
    with open(DATA, encoding="utf-8") as f:
        docs = [json.loads(line) for line in f if line.strip()]

    llm = _make_llm()
    done = 0
    for i, d in enumerate(docs):
        s = _gen_one(llm, d)
        if s:
            d["summary"] = s
            done += 1
            print(f"  [{i+1}/{len(docs)}] {d['tags']['file'][:32]:32} → {s[:50]}...")
        else:
            print(f"  [{i+1}/{len(docs)}] {d['tags']['file'][:32]:32} → 跳过(留旧摘要)")

    missing = [i for i, d in enumerate(docs) if not d["summary"]]
    print(f"\n完成: {done}/{len(docs)} 重写为文档级 summary; 缺失 {len(missing)} 个(可重跑)")
    with open(DATA, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"输出: {DATA}")


if __name__ == "__main__":
    main()
