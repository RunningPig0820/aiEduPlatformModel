"""
rag-system 分库 jsonl - 切片数据/**/切片/*.md → rag_slices-rag-system.jsonl

按功能独立脚本(分库)。切片头两种格式都处理:
- 格式A(语雀/引导问题/OpenSpec): summary/权威度/模块/COS路径/类别 各一行, 无来源/锚点/节
  → source 从路径顶层目录推导, section 从文件名入口段切前缀, anchor 取 `# 标题`
- 格式B(代码/坑档案): summary/来源｜锚点/节/COS路径/类别/target, authority 无头默认 0.8

机器元信息(entry_id/source_doc)摄入时从文件名+层配置推导(见 切片数据/readme.md), md 头不写。

用法: cd ai-edu-ai-service && venv/bin/python scripts/rag/knowledge-graph/01_slice_jsonl.py
输入: docs/rag/knowledge-graph/切片数据/**/切片/*.md
输出: scripts/rag/data/rag_slices-knowledge-graph.jsonl
"""
import glob
import json
import logging
import os
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/rag-system"
SLICES = os.path.join(CORPUS, "切片数据")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "rag_slices-rag-system.jsonl")
MIN_CHARS = 60

MODULE = "rag-system"
# 文件名入口段标记(用于从格式A文件名切 section 前缀)
ENTRY_MARKERS = re.compile(
    r"-(?:D\d+|选型\d+|场景\d+|阶段\d+|问题\d+|总揽-\d+|"
    r"Goals-Non-Goals|Context|开放问题|迁移计划|风险与权衡|验收反馈|\d+)-"
)


def _field(line: str, key: str) -> str | None:
    """从 `> key: 值` 取 值(兼容 半角:/全角：)。"""
    for colon in (":", "："):
        prefix = f"> {key}{colon}"
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def _section_from_filename(name: str) -> str:
    """格式A: 文件名入口段切前缀 → 源文档名。"""
    m = ENTRY_MARKERS.search(name)
    return name[:m.start()] if m else name


def parse_slice(path: str) -> dict | None:
    """单个切片 md → block dict; 头字段缺失/正文过短 → None。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    meta, body, header_done, title = {}, [], False, ""
    for ln in lines:
        s = ln.strip()
        if not header_done:
            if not s:
                continue
            if s.startswith("#"):
                if not title:
                    title = s.lstrip("#").strip()
                continue
            if s.startswith(">") and not s.startswith("---"):
                _KEYMAP = {"summary": "summary", "权威度": "authority", "模块": "module",
                           "COS路径": "cos_path", "类别": "category", "节": "section",
                           "来源": "source", "锚点": "anchor"}
                for part in s[1:].strip().split("｜"):
                    part = part.strip()
                    for cn, dst in _KEYMAP.items():
                        for colon in (":", "："):
                            if part.startswith(cn + colon):
                                meta[dst] = part[len(cn) + 1:].strip()
                                break
                continue
            if s.startswith("---"):
                header_done = True
                continue
            header_done = True
            body.append(ln)
        else:
            body.append(ln)

    text = "\n".join(body).strip()
    if len(text) < MIN_CHARS:
        logger.warning("[正文过短 %dB] %s", len(text), os.path.relpath(path, SLICES))
        return None

    name = os.path.basename(path).replace(".md", "")
    rel = os.path.relpath(path, SLICES)
    source = rel.split(os.sep)[0]

    # authority 头可能带后缀说明(如 `1.0（合成问答答案切片，非原始证据）`), 提取数字
    _auth = 0.8
    if meta.get("authority"):
        m = re.search(r"\d+(?:\.\d+)?", meta["authority"])
        if m:
            _auth = float(m.group())

    block = {
        "text": text,
        "summary": meta.get("summary", ""),
        "tags": {
            "module": meta.get("module") or MODULE,
            "category": meta.get("category", ""),
            "source": source,
            "authority": _auth,
            "section": meta.get("section") or _section_from_filename(name),
            "file": name,
            "file_path": meta.get("cos_path", ""),
            "anchor": meta.get("anchor") or title,
            "pool": "slice",
            "embed_mode": "full",   # 切片池全部全文向量化(块 ≤5000 已校验)
        },
    }
    return block


def main():
    files = [p for p in glob.glob(os.path.join(SLICES, "**", "切片", "*.md"), recursive=True)
             if os.path.basename(p) != "readme.md"]
    blocks = [b for b in (parse_slice(p) for p in files) if b]
    blocks.sort(key=lambda b: (b["tags"]["source"], b["tags"]["file"]))

    missing = [(b["tags"]["file"], k) for b in blocks
               for k in ("summary", "authority", "source", "anchor", "module", "section", "file_path", "category")
               if (b["summary"] if k == "summary" else b["tags"].get(k)) in ("", None)]
    if missing:
        logger.warning("[头缺失 %d 处] %s", len(missing), missing[:5])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for b in blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    from collections import Counter
    logger.info("输出 %d 块(pool=slice): %s", len(blocks), OUT)
    logger.info("source 分布: %s", dict(Counter(b["tags"]["source"] for b in blocks)))


if __name__ == "__main__":
    main()
