"""
rag-system 全量库 jsonl - 源文档(1.语雀/3.代码/4.完善文档) → rag_slices_full-rag-system.jsonl

与 knowledge-graph 02_full_jsonl 差异:
1. 完善文档 9 份**整篇一块**(text 2166~4836 ≤5000, 全部全文向量化, 不拆块)
2. 代码分析 9 份无 CLI 小节, 整篇一条(>5000 条件式只 embed summary)
3. 语雀 6 份整篇一条(大文件条件式只 embed summary)

embed_mode 标记: summary+全文 ≤5000 → full(embed 全文), 超限 → summary(只 embed summary)。
对齐 cos向量桶的字段.md 第7节 大文档摘要召回机制。

用法: cd ai-edu-ai-service && venv/bin/python scripts/rag/rag-system/02_full_jsonl.py
输入: docs/rag/rag-system/{1.语雀,3.代码,4.完善文档}/*.md
输出: scripts/rag/data/rag_slices_full-rag-system.jsonl
"""
import glob
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/rag-system"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "rag_slices_full-rag-system.jsonl")
MODULE = "rag-system"
FULL_EMBED_MAX_CHARS = 5000  # 全量池条件式阈值(与 build_index.py 一致)

# 源目录 → (source, 默认 authority, 形态); 全 whole = 整篇一条(完善/代码/语雀)
LAYERS = {
    "1.语雀":    ("语雀",     0.8, "whole"),
    "3.代码":    ("代码",     0.8, "whole"),
    "4.完善文档": ("完善文档",  1.0, "whole"),
}


def _field(line: str, key: str) -> str | None:
    for colon in (":", "："):
        prefix = f"> {key}{colon}"
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def parse_doc(path: str):
    """头字段 + 正文行(剥标题/头元信息), 返回 (meta, body_lines, name)。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    meta, body, header_done = {}, [], False
    for ln in lines:
        s = ln.strip()
        if not header_done:
            if not s or s.startswith("---"):
                continue
            if s.startswith("#"):
                continue
            if s.startswith(">"):
                for key, dst in (("summary", "summary"), ("COS路径", "cos_path"),
                                 ("类别", "category"), ("权威度", "authority")):
                    v = _field(s, key)
                    if v:
                        meta[dst] = v
                continue
            header_done = True
            body.append(ln)
        else:
            body.append(ln)
    name = os.path.basename(path).replace(".md", "")
    return meta, body, name


def _section(name: str, source: str) -> str:
    if source == "完善文档":
        return name.split("-", 1)[0]                # 01-产品定位 → 01
    if source == "代码":
        return name.split("-", 1)[0]                # 分析-01-... → 分析-01
    return name                                     # 语雀-决策记录


def main():
    blocks = []
    for dirname, (source, default_authority, form) in LAYERS.items():
        for p in sorted(glob.glob(os.path.join(CORPUS, dirname, "*.md"))):
            meta, body, name = parse_doc(p)
            category = meta.get("category", "")
            cos_path = meta.get("cos_path", "")
            authority = meta.get("authority") or default_authority
            summary = meta.get("summary", "")
            text = "\n".join(body).strip()
            if not text:
                logger.warning("[空正文] %s", name)
                continue
            embed_mode = "full" if len(summary) + len(text) <= FULL_EMBED_MAX_CHARS else "summary"
            blocks.append({
                "text": text,
                "summary": summary,
                "tags": {
                    "module": MODULE,
                    "category": category,
                    "source": source,
                    "authority": float(authority) if authority else default_authority,
                    "section": _section(name, source),
                    "file": name,
                    "file_path": cos_path,
                    "anchor": name,
                    "pool": "full",
                    "embed_mode": embed_mode,
                },
            })
            logger.info("  %s | text %d 字符 | summary %d 字 | embed_mode=%s",
                        name, len(text), len(summary), embed_mode)

    missing = [(b["tags"]["file"], k) for b in blocks
               for k in ("summary", "source", "anchor", "module", "section", "category")
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
    logger.info("embed_mode 分布: %s", dict(Counter(b["tags"]["embed_mode"] for b in blocks)))


if __name__ == "__main__":
    main()
