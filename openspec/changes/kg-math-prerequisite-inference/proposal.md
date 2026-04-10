> **执行顺序: 4/5** | **设计成本: 有** (LLM 调用) | **前置依赖: 无**

## Why

前置关系推断是知识图谱项目的**核心设计成本**部分。当前 EduKG 数据只有关联关系（RELATED_TO），没有学习依赖关系（PREREQUISITE）。

学习依赖关系需要通过以下方式构建：
1. **教材顺序推断**：基于教材章节顺序生成 TEACHES_BEFORE
2. **定义依赖抽取**：从知识点定义文本中匹配其他知识点名称
3. **LLM 多模型投票**：GLM-4-flash + DeepSeek 两模型一致才采纳

**重要区别**：
- **TEACHES_BEFORE ≠ PREREQUISITE**：教材教学顺序 ≠ 学习依赖
- 例：教材可能先教"集合"再教"函数"，但学"函数"不一定要先学"集合"

**业务价值**：
- 支持"学习路径推荐"
- 支持"前置知识检测"
- 支持"个性化学习顺序"

## What Changes

### 1. 双模型投票核心模块 (`edukg/core/llm_inference/`)

```
edukg/core/llm_inference/
├── __init__.py
├── dual_model_voter.py      # 双模型投票核心逻辑
├── prompt_templates.py       # LLM Prompt 模板
├── prerequisite_inferer.py   # 前置关系推断
├── definition_extractor.py   # 定义依赖抽取（可选）
├── teaches_before_inferer.py # 教学顺序推断（可选）
└── config.py                 # 配置
```

**核心能力**：
- `DualModelVoter`: 双模型投票器（GLM-4-flash + DeepSeek）
- `PrerequisiteInferer`: 前置关系推断器
- `PromptTemplates`: Prompt 模板集合

### 2. 命令行入口 (`edukg/scripts/kg_inference/`)

```
edukg/scripts/kg_inference/
├── infer_prerequisites.py    # 前置关系推断入口
└── validate_dag.py           # DAG 验证入口
```

### 3. 输出 JSON 文件（手动导入）

```
edukg/data/edukg/math/6_推理结果/output/
├── teaches_before.json       # TEACHES_BEFORE 关系
├── llm_prereq.json           # LLM 推断的前置关系
├── final_prereq.json         # 融合后的最终前置关系
└── validation_report.json    # DAG 验证报告
```

## Capabilities

### New Capabilities

- `dual-model-voter`: 双模型投票能力（GLM-4-flash + DeepSeek）
- `prerequisite-inference`: 前置关系推断能力
- `dag-validation`: DAG 验证能力

### Reused By

- `kg-math-complete-graph`: 复用双模型投票进行知识点匹配

## Impact

- **新模块**: `edukg/core/llm_inference/`
- **新脚本**: `edukg/scripts/kg_inference/`
- **输出文件**: JSON 格式，手动验证后导入 Neo4j
- **LLM 调用**: 约 8,980 次（使用免费/低成本模型）
- **依赖**: 无前置依赖，可独立开发