"""
1.5 切片数据 md 落盘 - 将 rag_slices.jsonl 的块导出为可读 md 文件

切好的块按 md 格式输出到 `docs/rag/ai-tutoring/切片数据/`：
- 按来源/文件夹组织: 完善文档 / 语雀 / OpenSpec / 代码 / 坑档案
- 每块一个 md 文件: 文件名 = <file>-<锚点>.md (完善文档整文件一块, 即 <file>.md)
- 文件头带 summary + 标签(权威度/来源/锚点/节), 正文随块

用途: 人可读审查切片质量 + 向量入库前校验(jsonl 为索引入口, md 为审查视图)。

用法: cd ai-edu-ai-service && python scripts/rag/export_slices_md.py
输入: scripts/rag/data/rag_slices.jsonl
输出: docs/rag/ai-tutoring/切片数据/
"""
import json
import os
import re
import shutil

DATA = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl")
OUT_DIR = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/ai-tutoring/切片数据"

# 来源 -> 输出子文件夹(路径里已含编号, 输出目录用纯名)
SOURCE_DIR = {
    "完善文档": "完善文档",
    "语雀": "语雀",
    "OpenSpec": "OpenSpec",
    "代码": "代码",
    "坑档案": "坑档案",
}

ILLEGAL = re.compile(r'[\\/:*?"<>|\s]+')
DUMP = re.compile(r"-+")


def slug(s: str) -> str:
    """锚点 -> 文件系统安全片段(保留中文, 非法字符/空白转 -)"""
    s = ILLEGAL.sub("-", s.strip())
    s = DUMP.sub("-", s)
    return s.strip("-")[:80].rstrip("-")


def block_md(b: dict) -> str:
    t = b["tags"]
    title = t["file"]
    summary = b.get("summary", "") or "(无 summary)"
    lines = [
        f"# {title}",
        "",
        f"> summary: {summary}",
        f"> 权威度: {t['authority']} ｜ 来源: {t['source']} ｜ 锚点: {t['anchor']}",
        f"> 模块: {t['module']} ｜ 节: {t['section']}",
        "",
        "---",
        "",
        b["text"].strip(),
        "",
    ]
    return "\n".join(lines)


def block_filename(b: dict) -> str:
    t = b["tags"]
    if t["source"] == "完善文档":
        # 整文件一块, 锚点==文件名, 直接 <file>.md
        return f"{t['file']}.md"
    return f"{t['file']}-{slug(t['anchor'])}.md"


def main():
    with open(DATA, encoding="utf-8") as f:
        blocks = [json.loads(line) for line in f if line.strip()]

    # 清空重建, 保证幂等(旧文件不残留)
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    written = 0
    by_source = {}
    used = {}  # 子目录内已用文件名 -> 出现次数, 冲突时加 -2/-3 防覆盖
    for b in blocks:
        t = b["tags"]
        sub = SOURCE_DIR.get(t["source"], "其他")
        d = os.path.join(OUT_DIR, sub)
        os.makedirs(d, exist_ok=True)
        name = block_filename(b)
        used[name] = used.get(name, 0) + 1
        if used[name] > 1:
            stem, ext = os.path.splitext(name)
            name = f"{stem}-{used[name]}{ext}"
        path = os.path.join(d, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(block_md(b))
        written += 1
        by_source[t["source"]] = by_source.get(t["source"], 0) + 1

    # 顶层 README 说明
    readme = (
        "# 切片数据\n\n"
        "> 由 `ai-edu-ai-service/scripts/rag/export_slices_md.py` 从 `rag_slices.jsonl` 导出"
        "(2026-08-24)。\n"
        "> 用途: **人可读审查切片质量** + 向量入库前校验。索引入口仍是 `data/rag_slices.jsonl`,"
        "此处为 md 审查视图。\n\n"
        "| 来源 | 权威度 | 块数 |\n|---|---|---|\n"
    )
    order = ["完善文档", "语雀", "OpenSpec", "代码", "坑档案"]
    for s in order:
        n = by_source.get(s, 0)
        authority = {"完善文档": 1.0, "语雀": 0.7, "OpenSpec": 0.7, "代码": 0.8, "坑档案": 0.8}[s]
        readme += f"| {s} | {authority} | {n} |\n"
    readme += f"\n合计: **{written} 块**\n"
    with open(os.path.join(OUT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"导出完成: {written} 块 → {OUT_DIR}")
    for s in order:
        print(f"  {s:6s}: {by_source.get(s, 0)} 块")


if __name__ == "__main__":
    main()
