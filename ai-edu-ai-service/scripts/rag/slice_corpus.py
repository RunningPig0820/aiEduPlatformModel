"""
1.5 切片脚本 - 按 `docs/rag/ai-tutoring/切片清单.md` + `tasks.md 1.5A` 定稿逻辑切块

规则(2026-08-24 定稿):
- 完善文档(权威1.0): 整文件一块(一节=一个问题答案, 不细切)
- 语雀(0.7): 按 h2 切, 保留标注块
- OpenSpec design(0.7): 按 h3 决策切; Risks/Migration/OpenQuestions/NonGoals 段过滤不切
- 代码分析(0.8): 按 h2 切
- 坑档案(0.8): 按 h3 每坑一块

每块含 summary 占位(由 gen_summaries.py 用 LLM 填充"解决什么问题"一句话)。
输出: scripts/rag/data/rag_slices.jsonl  (每行 {text, summary, tags})

用法: cd ai-edu-ai-service && python scripts/rag/slice_corpus.py
"""
import json
import os
import re

CORPUS = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/ai-tutoring"
OUT = os.path.join(os.path.dirname(__file__), "data", "rag_slices.jsonl")

MIN_CHARS = 60        # 低于此长度的块(纯标题/空)丢弃
MAX_CHARS_FILE = 12000   # 整文件块(完善文档=一个问题的完整答案, 含追问与防御, 不截断)
MAX_CHARS_SPLIT = 6000   # 按标题切的块上限: 超限按段落拆成多块(不丢尾部), 原 2000 会截掉尾段
SPLIT_RE = re.compile(r"^(#{1,4})\s+(.*)$")

# (glob, authority, source, split_level, mode)
#   mode="file" 整文件一块; mode="split" 按标题切
LAYERS = [
    ("4.完善文档/*.md", 1.0, "完善文档", 0, "file"),
    ("1.语雀/*.md", 0.7, "语雀", 2, "split"),
    ("2.OpenSpec design 决策/design-*.md", 0.7, "OpenSpec", 3, "split"),
    ("3.代码/分析-*.md", 0.8, "代码", 2, "split"),
    ("5.难点/坑档案.md", 0.8, "坑档案", 3, "split"),
]

# OpenSpec 段级过滤(面试价值低, 整段不切)
DISCARD_HEADS = {"Risks / Trade-offs", "Risks", "Migration Plan", "Open Questions",
                 "Non-Goals", "Goals", "Migration Plan", "Migration"}
DISCARD_PREFIX = ("Risk", "Open Question", "Migration", "Non-Goals")


def find_files(pattern: str):
    base, pat = pattern.split("/", 1)
    d = os.path.join(CORPUS, base)
    if not os.path.isdir(d):
        return []
    return sorted(os.path.join(d, f) for f in os.listdir(d)
                  if __import__("fnmatch").fnmatch(f, pat))


def section_of(path: str) -> str:
    """完善文档取节号(01~08), 其余取文件名"""
    name = os.path.basename(path)
    if re.match(r"^\d\d-", name):
        return name.split("-", 1)[0]
    return name.replace(".md", "")


def _tags(path: str, authority: float, source: str, anchor: str,
          module: str = "ai-tutoring") -> dict:
    """块 metadata; module = 模块锚点闭集 id(三端定稿: ai-tutoring/knowledge-graph/question-analysis/rag-system)。
    默认 ai-tutoring 向后兼容; 多模块切片时按闭集 id 传(select_corpus 按 tags.module 选池, 不依赖目录名)。"""
    return {
        "module": module,
        "section": section_of(path),
        "source": source,
        "authority": authority,
        "file": os.path.basename(path).replace(".md", ""),
        # 相对语料根 docs/rag/ai-tutoring/ 的路径(前端定位源文件展示内容; 1.6A 新增)
        "file_path": os.path.relpath(path, CORPUS).replace(os.sep, "/"),
        "anchor": anchor,
    }


def chunk_paragraphs(text: str, cap: int) -> list:
    """超长块按段落拆多块: 空行分段贪心合并到<=cap; 单段仍超cap按 cap 硬切(保尾部进索引)"""
    paras = re.split(r"\n\s*\n", text.strip())
    chunks, cur = [], ""
    for p in paras:
        p = p.strip()
        if not p:
            continue
        if cur and len(cur) + len(p) + 1 > cap:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
        while len(cur) > cap:  # 超长单段保护
            chunks.append(cur[:cap])
            cur = cur[cap:]
    if cur:
        chunks.append(cur)
    return chunks


def slice_file(path: str, authority: float, source: str, split_level: int, mode: str,
               module: str = "ai-tutoring") -> list:
    """切片单文件 → 块列表; module = 模块闭集 id(默认 ai-tutoring, 多模块切片时传 rag-system 等)。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    title = os.path.basename(path).replace(".md", "")

    if mode == "file":
        # 整文件一块: 去掉 # 标题行, 正文 = 全部内容
        body = [ln for ln in lines if not ln.startswith("#")]
        text = "\n".join(body).strip()
        if len(text) < MIN_CHARS:
            return []
        if len(text) > MAX_CHARS_FILE:
            text = text[:MAX_CHARS_FILE] + "\n\n[已截断]"
        return [{"text": text, "summary": "", "tags": _tags(path, authority, source, title, module)}]

    # mode="split": 按标题切, 块起点 = level<=split_level; OpenSpec 过滤 discard 段
    blocks, cur_anchor, cur_lines = [], None, []
    discarding = False
    for ln in lines:
        m = SPLIT_RE.match(ln)
        if m:
            level = len(m.group(1))
            heading = m.group(2).strip()
            if level <= split_level:
                if cur_anchor is not None:
                    blocks.append((cur_anchor, cur_lines))
                discarding = source == "OpenSpec" and (
                    heading in DISCARD_HEADS or heading.startswith(DISCARD_PREFIX))
                cur_anchor = heading
                cur_lines = [ln] if not discarding else []
                continue
            if cur_anchor is None:
                cur_anchor = heading
                cur_lines = [ln] if not discarding else []
            elif not discarding:
                cur_lines.append(ln)
            continue
        if cur_anchor is None or discarding:
            continue
        cur_lines.append(ln)
    if cur_anchor is not None and not discarding:
        blocks.append((cur_anchor, cur_lines))

    out = []
    for anchor, blines in blocks:
        text = "\n".join(blines).strip()
        if len(text) < MIN_CHARS:
            continue
        if len(text) > MAX_CHARS_SPLIT:
            # 段落拆块(同锚点, md 导出由冲突序号区分文件名; summary 同节共享)
            for chunk in chunk_paragraphs(text, MAX_CHARS_SPLIT):
                out.append({"text": chunk, "summary": "", "tags": _tags(path, authority, source, anchor, module)})
        else:
            out.append({"text": text, "summary": "", "tags": _tags(path, authority, source, anchor, module)})
    return out


def main():
    all_blocks = []
    for pattern, authority, source, split_level, mode in LAYERS:
        for path in find_files(pattern):
            blocks = slice_file(path, authority, source, split_level, mode)
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
