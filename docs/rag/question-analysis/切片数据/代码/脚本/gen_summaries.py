"""
1.5 切片块摘要生成 - LLM 推断(doubao), 为每块写"解决什么问题"一句话

每块 summary 写给向量检索看(embedding 用 summary+text 拼接): 站在"面试问答检索"角度,
输出"这块解决什么问题"。批量(一次带 N 块, 输出 JSON list), 关思考(快) + 20s 超时 + 关重试。

用法: cd ai-edu-ai-service && python scripts/rag/gen_summaries.py
输入: scripts/rag/data/rag_slices.jsonl
输出: scripts/rag/data/rag_slices.jsonl (summary 字段填充)
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

DATA = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl")
BATCH = 5  # 每批块数

_SYSTEM = """你是 RAG 切片摘要器。对给定的每个"切片块"，输出一句话 summary：
- 站在"面试问答检索"角度，说明"这块解决什么问题 / 讲什么"
- 只输出 JSON 数组，格式 [{"index":0,"summary":"..."}, ...]，不要多余文字
- 一句话，30 字以内，口语、能命中问题关键词"""


def _make_llm():
    return LLMFactory.create(
        "doubao", settings.TUTORING_DECIDE_MODEL, temperature=0.0,
        extra_body={"thinking": {"type": "disabled"}},
        request_timeout=20, max_retries=0,
    )


def _gen_batch(llm, blocks: list):
    """一批块 → summary list; 失败返回 None(该批留空, 可重跑)"""
    items = [
        {"index": i, "text": (b["tags"]["file"] + " | " + b["tags"]["anchor"] + "\n" + b["text"])[:800]}
        for i, b in enumerate(blocks)
    ]
    prompt = json.dumps(items, ensure_ascii=False)[:12000]
    try:
        resp = llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=prompt),
        ])
        out = json.loads(resp.content)
        return {o["index"]: o["summary"].strip() for o in out}
    except Exception as e:
        logger.warning("summary 批量生成失败: %s", e)
        return None


def main():
    with open(DATA, encoding="utf-8") as f:
        blocks = [json.loads(line) for line in f if line.strip()]

    llm = _make_llm()
    done = 0
    for start in range(0, len(blocks), BATCH):
        batch = blocks[start:start + BATCH]
        mapping = _gen_batch(llm, batch)
        if mapping:
            for i, b in enumerate(batch):
                if i in mapping:
                    b["summary"] = mapping[i]
                    done += 1
        print(f"  批 {start // BATCH + 1}/{(len(blocks) + BATCH - 1) // BATCH}: 已生成 {done}/{len(blocks)}")

    missing = [i for i, b in enumerate(blocks) if not b["summary"]]
    print(f"\n完成: {done}/{len(blocks)} 有 summary; 缺失 {len(missing)} 个(可重跑)")
    with open(DATA, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    print(f"输出: {DATA}")


if __name__ == "__main__":
    main()
