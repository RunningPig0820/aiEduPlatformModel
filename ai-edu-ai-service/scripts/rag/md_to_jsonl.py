"""
阶段3 D1 切片池 jsonl 生成 - 切片数据/ 已切 md → rag_slices.jsonl

"切归切、改归改"：切片源头 = `docs/rag/ai-tutoring/切片数据/**/*.md`（已定稿、带
summary/类别/COS路径 头），不再重跑 slice_corpus。每个 md 文件 = 一块。

逆解析 export_slices_md.py 的写出格式（标题 + `>` 头 + `---` + text）：
  - `# <title>` 首行 → 跳过
  - `> summary: / 权威度｜来源｜锚点 / 模块｜节 / COS路径 / 类别` → tags
  - `---` 分隔符 / 引导问题的 `## 回答` 标题 → 跳过
  - 其余 → text（含 `##`/`###` 节标题，与旧 jsonl 块 text 一致）
file_path = 头里 `> COS路径:`（阶段2 定稿 COS key），tags.pool = "slice"。

用法: cd ai-edu-ai-service && python scripts/rag/md_to_jsonl.py
输入: docs/rag/ai-tutoring/切片数据/**/*.md
输出: scripts/rag/data/rag_slices.jsonl（覆盖；先备份旧 jsonl）
对齐: 每模块流水线-tasks.md 1.13 D1
"""
import json
import logging
import os
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/ai-tutoring"
SLICES = os.path.join(CORPUS, "切片数据")
OUT = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl")
MIN_CHARS = 60

HEADER_FIELD = re.compile(r"^>\s*(.*)$")
SEP = re.compile(r"^---+\s*$")


def _parse_field(part: str, key: str) -> str:
    """从 `key: 值` 片段取值(兼容 全角: 半角:)。"""
    part = part.strip()
    for colon in (":", "："):
        if part.startswith(key + colon):
            return part[len(key) + 1:].strip()
    return ""


def parse_md(path: str) -> dict | None:
    """解析单个切片 md → block dict; 头字段缺失/正文过短 → None。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    meta = {}
    body = []
    header_done = False
    for ln in lines:
        if not header_done:
            s = ln.strip()
            if not s:
                continue                      # 头部空行跳过
            if s.startswith("#"):
                if s.startswith("## 回答"):
                    header_done = True        # 引导问题: 正文在 ## 回答 之后
                continue                      # # 标题行跳过
            m = HEADER_FIELD.match(ln)
            if m and not SEP.match(s):
                body_s = m.group(1).strip()
                if body_s.startswith("summary:"):
                    meta["summary"] = body_s[len("summary:"):].strip()
                elif body_s.startswith("COS路径"):
                    meta["cos_path"] = body_s.split(":", 1)[-1].strip().lstrip("/")
                elif body_s.startswith("类别"):
                    meta["category"] = _parse_field(body_s, "类别") or body_s.split(":", 1)[-1].strip()
                elif "权威度" in body_s:
                    # 中文标签 → 英文 tags 键(authority/source/anchor)
                    for part in body_s.split("｜"):
                        for cn, eng in (("权威度", "authority"), ("来源", "source"),
                                        ("锚点", "anchor")):
                            v = _parse_field(part, cn)
                            if v:
                                meta[eng] = v
                    try:
                        meta["authority"] = float(meta["authority"])
                    except (KeyError, ValueError):
                        meta["authority"] = 0.7
                elif "模块" in body_s:
                    for part in body_s.split("｜"):
                        v = _parse_field(part, "模块")
                        if v:
                            meta["module"] = v
                        v = _parse_field(part, "节")
                        if v:
                            meta["section"] = v
                continue
            # 分隔符或正文首行
            if SEP.match(s):
                header_done = True
                continue
            header_done = True
            body.append(ln)
        else:
            body.append(ln)

    text = "\n".join(body).strip()
    if len(text) < MIN_CHARS:
        return None

    base = os.path.basename(path).replace(".md", "")
    missing = [k for k in ("summary", "authority", "source", "anchor", "module",
                           "section", "cos_path", "category") if k not in meta]
    if missing:
        logger.warning("[头缺失 %s] %s", ",".join(missing), os.path.relpath(path, SLICES))

    # 引导问题: summary 直接用问题标题(anchor), 不读 LLM 翻译版 `> summary:` 头——
    # 翻译版语义错位("AI答疑如何使用?"被翻成"学生端拍题/打字...使用闭环"), 导致
    # embedding/BM25 召不回(query 与翻译措辞语义远, 2026-08-26 实测 sim 0.65)。
    # 标题即"这段回答解决什么问题", 检索/展示都直观。
    summary = meta.get("summary", "")
    if meta.get("source") == "引导问题":
        summary = meta.get("anchor", base)

    tags = {
        "module": meta.get("module", "ai-tutoring"),
        "section": meta.get("section", ""),
        "source": meta.get("source", ""),
        "authority": meta.get("authority", 0.7),
        "file": base,
        "file_path": meta.get("cos_path", ""),
        "anchor": meta.get("anchor", base),
        "category": meta.get("category", ""),
        "pool": "slice",
    }
    return {"text": text, "summary": summary, "tags": tags}


def main() -> int:
    blocks, skipped = [], []
    for dirpath, _, filenames in os.walk(SLICES):
        for fn in sorted(filenames):
            if not fn.endswith(".md") or fn == "README.md":
                continue
            path = os.path.join(dirpath, fn)
            b = parse_md(path)
            if b:
                blocks.append(b)
            else:
                skipped.append(os.path.relpath(path, SLICES))

    with open(OUT, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    from collections import Counter
    by_src = Counter(b["tags"]["source"] for b in blocks)
    by_cat = Counter(b["tags"]["category"] for b in blocks)
    logger.info("写入 %s: %d 块（跳过 %d）", OUT, len(blocks), len(skipped))
    logger.info("来源分布: %s", dict(by_src))
    logger.info("类别分布: %s", dict(by_cat))
    for s in skipped:
        logger.warning("跳过: %s", s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
