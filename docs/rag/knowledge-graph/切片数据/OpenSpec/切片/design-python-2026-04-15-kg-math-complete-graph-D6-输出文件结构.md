# 输出文件结构

> summary: 输出文件结构：edukg/data/edukg/math/5_教材目录/output/下输出节点、关系、进度文件等JSON，供人工验证后导入。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D6-输出文件结构.md
> 类别：数据存储

---

### D6：输出文件结构

> 检索摘要：输出文件结构：edukg/data/edukg/math/5_教材目录/output/下输出节点、关系、进度文件等JSON，供人工验证后导入。

```
edukg/data/edukg/math/5_教材目录/output/
├── textbooks.json            # 教材节点
├── chapters.json             # 章节节点
├── sections.json             # 小节节点
├── textbook_kps.json         # 教材知识点节点
├── contains_relations.json   # CONTAINS 关系
├── in_unit_relations.json    # IN_UNIT 关系
├── matches_kg_relations.json # MATCHES_KG 关系（推理结果）
├── import_summary.json       # 导入统计摘要
└── progress/                 # 进度文件目录
    ├── infer_kp_state.json   # 教学知识点推断进度
    ├── match_kg_state.json   # 知识图谱匹配进度
    └── *.lock
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D6：输出文件结构）
