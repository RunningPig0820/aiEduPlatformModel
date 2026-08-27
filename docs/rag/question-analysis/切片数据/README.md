# 切片数据

> 由 `ai-edu-ai-service/scripts/rag/export_slices_md.py` 从对应 jsonl 导出的**人可读审查视图**。
> 用途: **人可读审查切片质量** + 向量入库前校验。索引入口仍是 jsonl，此处为 md 审查视图。
> 状态：本模块切片 jsonl 属 QT⑥（in_progress）——目录骨架先立，切片文件由 QT⑥ 导出后填充。

| 来源 | 权威度 | 进池 | doc_type | 切片前源 |
|---|---|---|---|---|
| 完善文档 | 1.0 | 全量池 rag-full | business_full_doc | `4.完善文档/01~09.md`（整篇不切） |
| 语雀 | 0.8 | 切片池 rag-slice | canonical | `1.语雀/语雀-*.md` |
| OpenSpec design | 0.7 | 切片池 rag-slice | design_spec | `2.OpenSpec design 决策/design-*.md` |
| 代码 | 0.8 | 切片池 rag-slice | code_analysis | `3.代码/分析-01~10.md` |
| 坑档案 | 0.8 | 切片池 rag-slice | 难点 | `5.难点/坑档案.md` |
| 引导问题 | 0.8 | 引导池（不进向量） | — | `7. 引导问题/`（问题列表 + 引导问题） |

> 各来源进库边界/切片口径以 `../切片清单.md` 为准；生成的各来源视图见 `代码/` `语雀/` `OpenSpec/` `坑档案/` `引导问题/` 子目录。
> 每个子目录 = `readme.md（来源切片说明）` + `处理方案/（该来源的生成/处理提示词与说明）`，参考 `1.语雀/处理方案/` 结构。