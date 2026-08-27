# 目录结构设计

> summary: 目录结构设计：核心代码放edukg/core/textbook与edukg/core/llm_inference，scripts仅做命令行入口，LLM推断复用dual_model_voter与textbook_kp_inferer。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D1-目录结构设计.md
> 类别：架构设计

---

### D1：目录结构设计

> 检索摘要：目录结构设计：核心代码放edukg/core/textbook与edukg/core/llm_inference，scripts仅做命令行入口，LLM推断复用dual_model_voter与textbook_kp_inferer。

**核心代码放入 `edukg/core/textbook/`**：

```
edukg/core/textbook/
├── __init__.py
├── config.py                # 配置（路径、URI版本等）
├── uri_generator.py         # URI 生成器
├── filters.py               # 知识点过滤规则
├── data_generator.py        # 数据生成器
├── kp_matcher.py            # 知识点匹配器
└── README.md                # 模块文档
```

**LLM 推断复用 `edukg/core/llm_inference/`**：

```
edukg/core/llm_inference/
├── dual_model_voter.py      # 双模型投票
├── textbook_kp_inferer.py   # 教学知识点推断（新增）
├── prompt_templates.py      # 提示词加载
└── prompts/
    ├── textbook_kg.txt      # 教学知识点推断提示词
    └── kp_match.txt         # 知识点匹配提示词
```

**scripts 只做命令行入口**：

```
edukg/scripts/kg_data/
├── generate_textbook_data.py   # 数据生成入口
├── infer_textbook_kp.py        # 教学知识点推断入口（新增）
└── match_textbook_kp.py        # 知识点匹配入口
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D1：目录结构设计）
