"""
阶段3 D2 全量池 jsonl - 语雀5 + 完善文档8 + 代码10 整篇一块 → rag_slices_full.jsonl

全量池管"整体/全局"问题(完整文档整篇一块, 不丢上下文), 与切片池(细节块)互补。
tags.pool = "full"; file_path = 源文件头 `> COS路径:`(阶段2 定稿 COS key)。

summary/category 复用旧 jsonl(bak-20260826)的 LLM 生成结果, 不重跑 LLM:
  - 完善文档: 旧 jsonl 整篇块已有 summary + category, 直接用
  - 语雀/代码: 该文件各切片块 summary 拼接(整篇"覆盖什么"), category 取多数

text: 源文件内容, 去 # 标题/小节行 + 开头 `>` 头块(COS路径/来源标记),
      保留正文块引用(> 行); 超 MAX_CHARS_FILE 截断(与 slice_corpus mode=file 一致)。

用法: cd ai-edu-ai-service && python scripts/rag/slice_full.py
输出: scripts/rag/data/rag_slices_full.jsonl (23 块)
对齐: 每模块流水线-tasks.md 1.13 D2
"""
import glob
import json
import logging
import os
import re
from collections import Counter

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/ai-tutoring"
OLD = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl.bak-20260826")
OUT = os.path.join(os.path.dirname(__file__), "data", "rag_slices_full.jsonl")
MIN_CHARS = 60
MAX_CHARS_FILE = 12000

LAYERS = [
    ("1.语雀/*.md", 0.7, "语雀"),
    ("4.完善文档/*.md", 1.0, "完善文档"),
    ("3.代码/分析-*.md", 0.8, "代码"),
]


def section_of(path: str) -> str:
    """完善文档取节号(01~08), 其余取文件名。与 slice_corpus.section_of 一致。"""
    name = os.path.basename(path)
    if re.match(r"^\d\d-", name):
        return name.split("-", 1)[0]
    return name.replace(".md", "")


def full_text(lines: list) -> str:
    """去 # 标题/小节行 + 开头 `>` 头块(COS路径/来源标记), 保留正文块引用。"""
    out, seen_body = [], False
    for ln in lines:
        s = ln.strip()
        if not seen_body and (s.startswith("#") or s.startswith(">")):
            continue                      # 标题 + 头部 > 头块
        seen_body = True
        if s.startswith("#"):
            continue                      # ## 小节标题行
        out.append(ln)
    return "\n".join(out).strip()


def parse_cos_path(lines: list) -> str:
    for ln in lines[:10]:
        s = ln.strip()
        if s.startswith("> COS路径"):
            return s.split(":", 1)[-1].strip().lstrip("/")
    return ""


def load_old_info() -> dict:
    """旧 jsonl → {(source, file): {summaries:[], cats:Counter()}}。"""
    info = {}
    for line in open(OLD, encoding="utf-8"):
        if not line.strip():
            continue
        b = json.loads(line)
        t = b["tags"]
        d = info.setdefault((t["source"], t["file"]), {"summaries": [], "cats": Counter()})
        if b.get("summary"):
            d["summaries"].append(b["summary"])
        d["cats"][t.get("category", "")] += 1
    return info


def main() -> int:
    old = load_old_info()
    blocks = []
    for pattern, authority, source in LAYERS:
        files = sorted(glob.glob(os.path.join(CORPUS, pattern)))
        for path in files:
            lines = open(path, encoding="utf-8").read().splitlines()
            text = full_text(lines)
            if len(text) < MIN_CHARS:
                logger.warning("跳过(太短): %s", os.path.relpath(path, CORPUS))
                continue
            if len(text) > MAX_CHARS_FILE:
                logger.warning("超长截断 %dB→%d: %s", len(text), MAX_CHARS_FILE,
                               os.path.relpath(path, CORPUS))
                text = text[:MAX_CHARS_FILE] + "\n\n[已截断]"
            base = os.path.basename(path).replace(".md", "")
            file_path = parse_cos_path(lines) or f"rag-source/ai-tutoring/{source}/{base}.md"
            d = old.get((source, base), {"summaries": [], "cats": Counter()})
            summary = "；".join(d["summaries"]) or ""
            cat = d["cats"].most_common(1)[0][0] if d["cats"] else ""
            tags = {
                "module": "ai-tutoring",
                "section": section_of(path),
                "source": source,
                "authority": authority,
                "file": base,
                "file_path": file_path,
                "anchor": base,
                "category": cat,
                "pool": "full",
            }
            blocks.append({"text": text, "summary": summary, "tags": tags})

    with open(OUT, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")
    by_src = Counter(b["tags"]["source"] for b in blocks)
    logger.info("写入 %s: %d 块", OUT, len(blocks))
    logger.info("来源分布: %s", dict(by_src))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
