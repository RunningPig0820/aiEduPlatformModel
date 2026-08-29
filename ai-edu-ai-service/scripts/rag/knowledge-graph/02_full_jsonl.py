"""
knowledge-graph 全量库 jsonl - 源文档(1.语雀/3.代码/4.完善文档) → rag_slices_full-knowledge-graph.jsonl

与 question-analysis 02_full_jsonl 的差异(用户 2026-08-29 定):
1. **完善文档 9 份按 `## ` 段拆块**(为什么/怎么设计/落地真相/追问与防御, 证据引用已删),
   每段一块 pool=full → 每块小(≤5000 字符)全部全文向量化; summary = 源文档 summary(回滚后的短版),
   每块共用(embed 前缀整篇语义锚 + 段文本细节)。
2. **代码 11 份过滤 `### CLI 入口` 小节**(无业务意义不入库), 其余整篇一条。
3. 语雀 9 份整篇一条, 大文件(>5000 字符)由 build_index 条件式只 embed(详细版 summary)。

用法: cd ai-edu-ai-service && venv/bin/python scripts/rag/knowledge-graph/02_full_jsonl.py
输入: docs/rag/knowledge-graph/{1.语雀,3.代码,4.完善文档}/*.md
输出: scripts/rag/data/rag_slices_full-knowledge-graph.jsonl
"""
import glob
import json
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/knowledge-graph"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "rag_slices_full-knowledge-graph.jsonl")
MODULE = "knowledge-graph"
FULL_EMBED_MAX_CHARS = 5000  # 全量池条件式阈值(与 build_index.py 一致): summary+全文 ≤5000 embed 全文, 超限只 embed summary

# 源目录 → (source, 默认 authority, 形态)
#   whole = 整篇一条;  code = 整篇一条但过滤 CLI 入口;  split = 按 ## 段拆块
LAYERS = {
    "1.语雀":    ("语雀",     0.8, "whole"),
    "3.代码":    ("代码",     0.8, "code"),
    "4.完善文档": ("完善文档",  1.0, "split"),
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
            if s.startswith("## "):
                # 完善文档: 正文首个 ## 段标题 → 正文开始(拆块需要保留标题)
                header_done = True
                body.append(ln)
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
        return name.split("-", 1)[0]                # 01-模块定位与核心价值 → 01
    if source == "代码":
        return name.split("-", 1)[0]                # 分析-01-... → 分析-01
    return name                                     # 语雀-决策记录 → 语雀-决策记录


def _filter_cli(body: list) -> list:
    """代码文档: 过滤 `### CLI 入口` 小节(到下一个 ###/## 前), 无业务意义不入库。"""
    out, skip = [], False
    for ln in body:
        s = ln.strip()
        if s.startswith("### CLI 入口"):
            skip = True
            continue
        if skip:
            if s.startswith("### ") or s.startswith("## "):
                skip = False
            else:
                continue
        out.append(ln)
    return out


def _split_sections(body: list) -> list[tuple[str, str]]:
    """完善文档: 按 `## ` 段拆块, 返回 [(title, section_text), ...]。"""
    blocks, cur_title, cur = [], None, []
    for ln in body:
        s = ln.strip()
        if s.startswith("## "):
            if cur:
                blocks.append((cur_title or "", "\n".join(cur)))
            cur_title = s[3:].strip()
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        blocks.append((cur_title or "", "\n".join(cur)))
    return [(t, txt.strip()) for t, txt in blocks if txt.strip()]


def _make_block(text: str, summary: str, source: str, authority, category: str,
                section: str, name: str, anchor: str, cos_path: str) -> dict:
    # embed_mode: 全量池条件式——summary+全文 ≤5000 embed 全文(full), 超限只 embed summary
    embed_mode = "full" if len(summary) + len(text) <= FULL_EMBED_MAX_CHARS else "summary"
    return {
        "text": text,
        "summary": summary,
        "tags": {
            "module": MODULE,
            "category": category,
            "source": source,
            "authority": float(authority) if authority else 0.8,
            "section": section,
            "file": name,
            "file_path": cos_path,
            "anchor": anchor,
            "pool": "full",
            "embed_mode": embed_mode,
        },
    }


def main():
    blocks = []
    for dirname, (source, default_authority, form) in LAYERS.items():
        for p in sorted(glob.glob(os.path.join(CORPUS, dirname, "*.md"))):
            meta, body, name = parse_doc(p)
            category = meta.get("category", "")
            cos_path = meta.get("cos_path", "")
            authority = meta.get("authority") or default_authority
            section = _section(name, source)
            summary = meta.get("summary", "")
            if not body:
                logger.warning("[空正文] %s", name)
                continue

            if form == "split":
                # 完善文档: 按段拆块, 全文向量化(每块小, 由 build_index embed(summary+全文))
                for title, text in _split_sections(body):
                    blocks.append(_make_block(text, summary, source, authority, category,
                                              section, name, title, cos_path))
                logger.info("  split %s | %d 块 | summary %d 字", source, len(_split_sections(body)), len(summary))
            elif form == "code":
                body = _filter_cli(body)
                text = "\n".join(body).strip()
                if not text:
                    logger.warning("[过滤后空] %s", name)
                    continue
                blocks.append(_make_block(text, summary, source, authority, category,
                                          section, name, name, cos_path))
                logger.info("  code  %s | text %d 字符 | summary %d 字 | CLI已滤", source, len(text), len(summary))
            else:
                text = "\n".join(body).strip()
                blocks.append(_make_block(text, summary, source, authority, category,
                                          section, name, name, cos_path))
                logger.info("  whole %s | text %d 字符 | summary %d 字", source, len(text), len(summary))

    missing = [(b["tags"]["file"], b["tags"]["anchor"], k) for b in blocks
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


if __name__ == "__main__":
    main()
