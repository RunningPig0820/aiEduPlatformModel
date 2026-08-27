# D1：目录结构设计
> summary: 目录结构设计：核心代码放edukg/core/llm_inference/，含dual_model_voter、prerequisite_inferer、textbook_kp_inferer与prompts，scripts仅做命令行入口。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-D1-目录结构设计.md
> 类别：数据关联

> 检索摘要：目录结构设计：核心代码放edukg/core/llm_inference/，含dual_model_voter、prerequisite_inferer、textbook_kp_inferer与prompts，scripts仅做命令行入口。

**核心代码放入 `edukg/core/llm_inference/`**：

```
edukg/core/llm_inference/
├── __init__.py              # 模块导出
├── config.py                # 配置（模型、阈值等）
├── prompt_templates.py      # Prompt 加载和格式化
├── dual_model_voter.py      # 双模型投票核心逻辑
├── prerequisite_inferer.py  # 前置关系推断
├── textbook_kp_inferer.py   # 教学知识点推断（新增）
├── README.md                # 模块文档
└── prompts/                 # 提示词文件目录（新增）
    ├── prerequisite.txt     # 前置关系推断提示词
    ├── kp_match.txt         # 知识点匹配提示词
    ├── definition_deps.txt  # 定义依赖抽取提示词
    └── textbook_kg.txt      # 教学知识点推断提示词
```

**scripts 只做命令行入口**：

```
edukg/scripts/kg_inference/
├── infer_prerequisites.py   # 前置关系推断入口
├── infer_textbook_kp.py     # 教学知识点推断入口（新增）
└── validate_dag.py          # DAG 验证入口
```

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D1：目录结构设计）
