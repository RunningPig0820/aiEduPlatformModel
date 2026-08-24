"""
1.5 切片脚本 - 按 `docs/rag/ai-tutoring/切片清单.md` 四层切块

输入: 四层语料(完善文档8 / 语雀5 / OpenSpec design11 / 代码分析10+坑档案)
处理: 按 markdown 标题切块(h2 为主, 坑档案用 h3), 打标签, 长度控制
输出: scripts/rag/data/rag_slices.jsonl  (每行 {text, tags})

用法: cd ai-edu-ai-service && python scripts/rag/slice_corpus.py
"""
import json
import os
import re

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/ai-tutoring"
OUT = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl")

MIN_CHARS = 60        # 低于此长度的块(纯标题/空)丢弃
MAX_CHARS = 2000      # 高于此长度截断(保留开头)
SPLIT_RE = re.compile(r"^(#{1,4})\s+(.*)$")

# 四层配置: (glob, authority, source, split_level)
#   split_level: 2 = 按 h2 切; 3 = 按 h3 切(坑档案每个坑一块)
LAYERS = [
    ("4.完善文档/*.md", 1.0, "完善文档", 2),
    ("1.语雀/*.md", 0.7, "语雀", 2),
    ("2.OpenSpec design 决策/design-*.md", 0.7, "OpenSpec", 2),
    ("3.代码/分析-*.md", 0.8, "代码", 2),
    ("5.难点/坑档案.md", 0.8, "坑档案", 3),
]


def find_files(pattern: str):
    base, pat = pattern.split("/", 1)
    d = os.path.join(CORPUS, base)
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d) if __import__("fnmatch").fnmatch(f, pat))


def section_of(path: str) -> str:
    """完善文档取节号(01~08), 其余取文件名"""
    name = os.path.basename(path)
    if name.startswith(("0", "1", "2", "3", "4", "5", "6", "7", "8")) and "-" in name:
        return name.split("-", 1)[0]
    return name.replace(".md", "")


def slice_file(path: str, authority: float, source: str, split_level: int) -> list:
    """按标题切块: 块起点 = level<=split_level 的标题; 内容累积到下一同/更高级标题"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    blocks = []          # (anchor, [lines])
    cur_anchor, cur_lines = None, []
    title = os.path.basename(path).replace(".md", "")

    for ln in lines:
        m = SPLIT_RE.match(ln)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            if level <= split_level:
                if cur_anchor is not None:
                    blocks.append((cur_anchor, cur_lines))
                cur_anchor = heading
                cur_lines = [ln]
                continue
            # 更深的标题并入当前块
            if cur_anchor is None:
                cur_anchor = heading
                cur_lines = [ln]
            else:
                cur_lines.append(ln)
            continue
        if cur_anchor is None:
            continue  # 文档头无标题前的杂项
        cur_lines.append(ln)

    if cur_anchor is not None:
        blocks.append((cur_anchor, cur_lines))

    out = []
    for anchor, blines in blocks:
        text = "\n".join(blines).strip()
        if len(text) < MIN_CHARS:
            continue
        if len(text) > MAX_CHARS:
            text = text[:MAX_CHARS] + "\n\n[已截断]"
        out.append({
            "text": text,
            "tags": {
                "module": "ai-tutoring",
                "section": section_of(path),
                "source": source,
                "authority": authority,
                "file": title,
                "anchor": anchor,
            },
        })
    return out


def main():
    all_blocks = []
    for pattern, authority, source, split_level in LAYERS:
        for path in find_files(pattern):
            blocks = slice_file(path, authority, source, split_level)
            all_blocks.extend(blocks)
            print(f"  {os.path.basename(path):45s} → {len(blocks):3d} 块")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for b in all_blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    srcs = {}
    for b in all_blocks:
        srcs[b["tags"]["source"]] = srcs.get(b["tags"]["source"], 0) + 1
    print(f"\n总块数: {len(all_blocks)}")
    print("按来源:", srcs)
    print(f"输出: {OUT}")


if __name__ == "__main__":
    main()
