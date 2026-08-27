# 切割脚本留档

> 用途：把生成 `切片数据/代码/` 视图所用的切割脚本复制留档，追溯"这些切片怎么切出来的"。源脚本在 `ai-edu-ai-service/scripts/rag/`，**以源为准**，此处为快照副本。

## 脚本清单与职责

| 脚本 | 职责 | 本模块用法 |
|---|---|---|
| `slice_corpus.py` | 语料 md → 切片池 jsonl（按 h2/h3 切） | `python scripts/rag/slice_corpus.py --module question-analysis --sources 代码` |
| `export_slices_md.py` | jsonl → 切片数据 md 人读视图 | `python scripts/rag/export_slices_md.py --module question-analysis` |
| `gen_summaries.py` | 块级 summary 自动生成（LLM） | 切片后跑，为每块补"解决什么问题"一句话 |
| `slice_full.py` | 全量池 jsonl（整篇一块） | 完善文档 1.0 用（全量池 rag-full） |
| `md_to_jsonl.py` | 切片数据 md → jsonl | 引导问题等结构化块解析 |
| `recover_slices.py` | 切片恢复工具 | 异常恢复用 |

## 当前切片状态（2026-08-27）

- 代码层：10 份分析文档 → **90 块**（每份 9 块 = 标题 + 8 个 h2 节，**全切不删**）
- jsonl：`ai-edu-ai-service/scripts/rag/data/rag_slices-question-analysis.jsonl`
- 视图：本目录 `../` 下 `代码/` 90 个块文件
- summary：块级 summary 待 `gen_summaries.py` 生成（当前 `(无 summary)`）

## 注意

- 脚本含硬编码 `ROOT` 路径，运行时需在 `ai-edu-ai-service/` 下用 venv python 执行（`cd ai-edu-ai-service && venv/bin/python ...`）
- 复制前两脚本已加 `--module` 参数化；其余脚本如要切其它来源（语雀/坑档案/引导问题）按需再参数化