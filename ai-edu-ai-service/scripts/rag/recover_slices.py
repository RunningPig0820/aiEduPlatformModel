"""
1.5 切片数据恢复 - 重建 rag_slices.jsonl (data/ 被删后无损恢复)

切片逻辑重跑(slice_corpus)生成块, summary 从 `切片数据/*.md` 文件头无损合并
(md 头带 summary/来源/锚点/节, 即给向量桶看的那份, 不重跑 LLM)。

用法: cd ai-edu-ai-service && python scripts/rag/recover_slices.py
输入: 语料(docs/rag/ai-tutoring) + 切片数据 md 审查视图
输出: scripts/rag/data/rag_slices.jsonl
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import slice_corpus

MD_DIR = "/Users/minzhang/Documents/work/ai/aiEduPlatformModel/docs/rag/ai-tutoring/切片数据"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rag_slices.jsonl")

HEAD_RE = re.compile(
    r"^> summary: (.*)$\n^> 权威度: (\S+) ｜ 来源: (\S+) ｜ 锚点: (.*)$\n^> 模块: (\S+) ｜ 节: (.*)$"
    r"\n\n---\n\n",
    re.M,
)


def read_md_summaries() -> dict:
    """(source, anchor) -> summary; 一个文件一块时 file 也参与"""
    out = {}
    for dirpath, _dirs, files in os.walk(MD_DIR):
        if os.path.basename(dirpath) == "切片数据":
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                head = f.read(2048)
            m = HEAD_RE.search(head)
            if not m:
                continue
            summary, authority, source, anchor, _module, section = m.groups()
            key = (source, anchor.strip())
            # 同锚点多块(段落拆块): 取非空 summary; 冲突取最长
            if key in out and (not summary or len(summary) <= len(out[key])):
                continue
            out[key] = summary.strip()
    return out


def main():
    summaries = read_md_summaries()
    print(f"从 md 头读到 summary: {len(summaries)} 条")

    new_blocks = []
    for pattern, authority, source, split_level, mode in slice_corpus.LAYERS:
        for path in slice_corpus.find_files(pattern):
            new_blocks.extend(slice_corpus.slice_file(path, authority, source, split_level, mode))

    matched = missed = 0
    for b in new_blocks:
        t = b["tags"]
        s = summaries.get((t["source"], t["anchor"]), "")
        if s:
            b["summary"] = s
            matched += 1
        else:
            missed += 1

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for b in new_blocks:
            f.write(json.dumps(b, ensure_ascii=False) + "\n")

    trunc = [b for b in new_blocks if "[已截断]" in b["text"]]
    print(f"恢复: {len(new_blocks)} 块 (应=234), summary {matched} 匹配 / {missed} 缺失, 截断 {len(trunc)}")
    print(f"输出: {OUT}")


if __name__ == "__main__":
    main()
