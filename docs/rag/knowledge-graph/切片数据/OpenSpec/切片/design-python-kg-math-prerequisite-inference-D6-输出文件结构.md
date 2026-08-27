# D6：输出文件结构
> summary: 输出文件结构：edukg/data/edukg/math/6_推理结果/output/下输出teaches_before、definition_deps、llm_prereq等JSON、validation_report与进度文件。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-D6-输出文件结构.md
> 类别：数据关联

> 检索摘要：输出文件结构：edukg/data/edukg/math/6_推理结果/output/下输出teaches_before、definition_deps、llm_prereq等JSON、validation_report与进度文件。

```
edukg/data/edukg/math/6_推理结果/output/
├── teaches_before.json       # TEACHES_BEFORE 关系
├── definition_deps.json      # 定义依赖
├── llm_prereq.json           # LLM 推断的前置关系
├── textbook_kps_inferred.json # 推断的教学知识点（新增）
├── final_prereq.json         # 融合后的最终前置关系
├── validation_report.json    # DAG 验证报告
└── progress/                 # 进度文件目录（新增）
    ├── prerequisite_state.json
    ├── textbook_kp_state.json
    └── *.lock
```

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D6：输出文件结构）
