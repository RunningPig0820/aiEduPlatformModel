# LLM 推理核心模块

双模型投票机制，用于前置关系推断和知识点匹配。

## 功能概述

本模块提供基于 LLM 的推理能力，核心特性：

- **双模型投票**：GLM-4-flash（免费）+ DeepSeek（低成本），两模型一致才采纳
- **前置关系推断**：判断知识点之间的学习依赖关系（PREREQUISITE）
- **知识点匹配**：判断不同来源的知识点是否表示同一概念
- **定义依赖抽取**：从知识点定义中识别依赖的其他知识点

## 目录结构

```
edukg/core/llm_inference/
├── __init__.py              # 模块导出
├── config.py                # 配置（模型名称、阈值、批量参数）
├── prompt_templates.py      # LLM Prompt 模板
├── dual_model_voter.py      # 双模型投票核心逻辑
└── prerequisite_inferer.py  # 前置关系推断器
```

## 核心组件

### 1. DualModelVoter - 双模型投票器

```python
from edukg.core.llm_inference import DualModelVoter

# 创建投票器
voter = DualModelVoter(
    primary_model="glm-4-flash",    # 免费
    secondary_model="deepseek-chat" # 低成本
)

# 执行投票
result = await voter.vote(prompt)

if result['consensus']:
    print(f"投票结果: {result['result']}")
    print(f"置信度: {result['confidence']}")
```

**投票规则**：
- 两模型一致 + confidence ≥ 0.8 → 接受（PREREQUISITE）
- 两模型一致 + confidence < 0.8 → 候选（PREREQUISITE_CANDIDATE）
- 两模型不一致 → 不采纳

### 2. PrerequisiteInferer - 前置关系推断器

```python
from edukg.core.llm_inference import PrerequisiteInferer

inferer = PrerequisiteInferer()

# 批量推断前置关系
kp_pairs = [
    {'kp_a': {'uri': 'A', 'name': '加法', 'description': '...'},
     'kp_b': {'uri': 'B', 'name': '乘法', 'description': '...'}},
]
results = await inferer.infer_batch(kp_pairs)

# 从教材顺序推断 TEACHES_BEFORE
teaches_before = inferer.infer_from_textbook_order(chapters)

# 从定义抽取依赖
deps = inferer.extract_from_definition(definition, kp_names)
```

### 3. Prompt 模板

```python
from edukg.core.llm_inference.prompt_templates import (
    PREREQUISITE_PROMPT,    # 前置关系推断
    KP_MATCH_PROMPT,        # 知识点匹配
    DEFINITION_DEPS_PROMPT, # 定义依赖抽取
    format_prerequisite_prompt,
    format_kp_match_prompt,
)
```

## 配置说明

`config.py` 中的主要配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `PRIMARY_MODEL` | `glm-4-flash` | 主模型（免费） |
| `SECONDARY_MODEL` | `deepseek-chat` | 副模型（DeepSeek-V3） |
| `CONFIDENCE_THRESHOLD_HIGH` | `0.8` | 高置信度阈值 |
| `CONFIDENCE_THRESHOLD_LOW` | `0.6` | 低置信度阈值 |
| `BATCH_SIZE` | `10` | 批处理大小 |
| `RATE_LIMIT_DELAY` | `1.0` | API 调用间隔（秒） |

## 使用场景

### 场景 1：前置关系推断

用于 `kg-math-prerequisite-inference` change：

```python
# 从 Neo4j 加载知识点
concepts = load_concepts_from_neo4j()

# 生成知识点对
pairs = generate_kp_pairs(concepts)

# 执行推断
results = await inferer.infer_batch(pairs)

# 保存结果
inferer.save_results(results, "llm_prereq.json")
```

### 场景 2：知识点匹配

用于 `kg-math-complete-graph` change：

```python
from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt

voter = DualModelVoter()

# 判断教材知识点与图谱知识点是否匹配
prompt = format_kp_match_prompt(
    textbook_kp_name="正数和负数的概念",
    textbook_kp_description="...",
    kg_kp_name="正数的定义",
    kg_kp_description="..."
)

result = await voter.vote(prompt)
if result['consensus'] and result['result']['decision']:
    print(f"匹配成功，置信度: {result['confidence']}")
```

## 命令行工具

### infer_prerequisites.py

```bash
# 估算成本
python edukg/scripts/kg_inference/infer_prerequisites.py --dry-run

# 执行推断
python edukg/scripts/kg_inference/infer_prerequisites.py

# 查看统计
python edukg/scripts/kg_inference/infer_prerequisites.py --stats
```

### validate_dag.py

```bash
# 验证 DAG 无环
python edukg/scripts/kg_inference/validate_dag.py

# 输出详细报告
python edukg/scripts/kg_inference/validate_dag.py --report
```

## 输出文件

所有输出文件位于 `edukg/data/edukg/math/6_推理结果/output/`：

| 文件 | 说明 |
|------|------|
| `teaches_before.json` | 教材教学顺序关系 |
| `definition_deps.json` | 定义依赖关系 |
| `llm_prereq.json` | LLM 推断的前置关系 |
| `final_prereq.json` | 融合后的最终前置关系 |
| `validation_report.json` | DAG 验证报告 |

## 成本估算

基于 1,295 个知识点：

- 预估知识点对：~2,590
- LLM 调用次数：~5,180（每个知识点对 2 个模型）
- GLM-4-flash：免费
- DeepSeek：约 0.003 元（0.001元/1000 tokens）

**总计成本：< 0.01 元**

## 依赖

- `ai-edu-ai-service/core/gateway/factory.py` - LLM Gateway
- `edukg/core/neo4j/client.py` - Neo4j 客户端
- `langchain-core` - LangChain 消息类型

## 测试

```bash
# 运行单元测试
pytest tests/core/llm_inference/ -v

# 测试数量：13 个
# 覆盖：投票逻辑、推断逻辑、DAG 验证
```

## 相关 Change

- **kg-math-prerequisite-inference**：前置关系推断（本模块）
- **kg-math-complete-graph**：教材数据导入（复用本模块的投票机制）