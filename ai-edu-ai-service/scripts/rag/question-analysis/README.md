# question-analysis 入库脚本

按功能分文件夹: 分库(切片池) / 全量库(源文档) 各自独立生成 jsonl, 复用 `scripts/rag/build_index.py` 引擎入 COS。

## 数据流

```
docs/rag/question-analysis/
├── 1.语雀(6) + 3.代码(10) + 4.完善文档(9)  ──▶ 02_full_jsonl.py ──▶ rag_slices_full-question-analysis.jsonl(25 条, pool=full)
└── 切片数据/**/切片/*.md(317)               ──▶ 01_slice_jsonl.py ──▶ rag_slices-question-analysis.jsonl(317 条, pool=slice)
                                                                              │
                                                                              ▼
                                                        build_index.py --module question-analysis --pool full|slice --clear
```

## 用法

```bash
cd ai-edu-ai-service

# 1. 分库 jsonl(317 切片, 覆盖旧的 90 条实验版)
venv/bin/python scripts/rag/question-analysis/01_slice_jsonl.py

# 2. 全量库 jsonl(25 源)
venv/bin/python scripts/rag/question-analysis/02_full_jsonl.py

# 3. 入桶(全量池 + 切片池, 各自 --clear 幂等重灌)
venv/bin/python scripts/rag/build_index.py --module question-analysis --pool full --clear
venv/bin/python scripts/rag/build_index.py --module question-analysis --pool slice --clear
```

## 切片头两种格式(01_slice_jsonl 都处理)

- **格式A(语雀/引导问题/OpenSpec)**: `summary/权威度/模块/COS路径/类别` 各一行, 无来源/锚点/节 → 从路径/文件名推导(source←顶层目录, authority←头或 0.8, section←文件名入口段前缀, anchor←`# 标题`)
- **格式B(代码/坑档案)**: `summary/来源｜锚点/节/COS路径/类别/target` → authority 无头给 0.8, source 从路径推导

## 全量库策略(02_full_jsonl)

- 语雀 6(4.6~29KB): 大文件 >5000 字符 → build_index 条件式 embed(详细 summary 790~1882 字作向量本体); 术语表小 → embed(summary+全文)
- 代码 10 + 完善文档 9(全 ≤5000): embed(summary+全文)
- authority: 完善文档 1.0 / 代码 0.8 / 语雀 0.8

## 输出

- `scripts/rag/data/rag_slices_full-question-analysis.jsonl`(25 条, pool=full)
- `scripts/rag/data/rag_slices-question-analysis.jsonl`(317 条, pool=slice)
