"""
question-analysis 全量库 jsonl - 源文档(1.语雀/3.代码/4.完善文档) → rag_slices_full-question-analysis.jsonl

按功能独立脚本(全量库)。25 个源文档整篇一块(pool=full):
- text = 全文正文(剥 # 标题 + > 头元信息), summary = 头 `> summary:`(语雀详细版/代码·完善文档锚点版)
- build_index 条件式: 大文件(语雀 5 份 >5000 字符)只 embed summary; 小文件 embed(summary+全文)

用法: cd ai-edu-ai-service && venv/bin/python scripts/rag/question-analysis/02_full_jsonl.py
输入: docs/rag/question-analysis/{1.语雀,3.代码,4.完善文档}/*.md
输出: scripts/rag/data/rag_slices_full-question-analysis.jsonl(25 条, pool=full)
"""
import glob
import json
import logging
import os
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/question-analysis"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "rag_slices_full-question-analysis.jsonl")
MODULE = "question-analysis"

# 源目录 → (source, 默认 authority)
LAYERS = {
    "1.语雀": ("语雀", 0.8),
    "3.代码": ("代码", 0.8),
    "4.完善文档": ("完善文档", 1.0),
}


def _field(line: str, key: str) -> str | None:
    for colon in (":", "："):
        prefix = f"> {key}{colon}"
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def _section(name: str, source: str) -> str:
    if source == "完善文档":
        return name.split("-", 1)[0]                # 05-数据落库与掌握度 → 05
    if source == "代码":
        return name.split("-", 1)[0]                # 分析-03-... → 分析-03
    return name                                     # 语雀-决策记录 → 语雀-决策记录


def parse_doc(path: str, source: str, default_authority: float) -> dict | None:
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    meta, body, header_done = {}, [], False
    for ln in lines:
        s = ln.strip()
        if not header_done:
            if not s:
                continue
            if s.startswith("#"):
                continue                              # # 标题跳过
            if s.startswith(">") and not s.startswith("---"):
                for key, dst in (("summary", "summary"), ("COS路径", "cos_path"),
                                 ("类别", "category"), ("权威度", "authority")):
                    v = _field(s, key)
                    if v:
                        meta[dst] = v
                continue
            header_done = True                        # 首个正文行
            body.append(ln)
        else:
            body.append(ln)

    text = "\n".join(body).strip()
    if not text:
        return None

    name = os.path.basename(path).replace(".md", "")
    return {
        "text": text,
        "summary": meta.get("summary", ""),
        "tags": {
            "module": MODULE,
            "category": meta.get("category", ""),
            "source": source,
            "authority": float(meta["authority"]) if meta.get("authority") else default_authority,
            "section": _section(name, source),
            "file": name,
            "file_path": meta.get("cos_path", ""),
            "anchor": name,
            "pool": "full",
        },
    }


def main():
    blocks = []
    for dirname, (source, authority) in LAYERS.items():
        for p in sorted(glob.glob(os.path.join(CORPUS, dirname, "*.md"))):
            b = parse_doc(p, source, authority)
            if b:
                blocks.append(b)
                logger.info("  %s | %s | text %d 字符 | summary %d 字",
                            source, os.path.basename(p), len(b["text"]), len(b["summary"]))

    missing = [(b["tags"]["file"], k) for b in blocks
               for k in ("summary", "file_path", "category")
               if (b["summary"] if k == "summary" else b["tags"].get(k)) in ("", None)]
    if missing:
        logger.warning("[头缺失 %d 处] %s", len(missing), missing[:5])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    from collections import Counter
    logger.info("输出 %d 块(pool=full): %s", len(blocks), OUT)
    logger.info("source 分布: %s", dict(Counter(b["tags"]["source"] for b in blocks)))


if __name__ == "__main__":
    main()
