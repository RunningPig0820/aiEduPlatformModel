# LLM 推理核心模块

基于双模型投票机制的 LLM 推理框架，用于知识图谱关系推断和知识点匹配。

## 功能概述

| 功能 | 描述 | 提示词 |
|------|------|--------|
| **前置关系推断** | 判断知识点之间的学习依赖关系（PREREQUISITE） | `prerequisite.txt` |
| **知识点匹配** | 判断不同来源的知识点是否表示同一概念 | `kp_match.txt` |
| **定义依赖抽取** | 从知识点定义中识别依赖的其他知识点 | `definition_deps.txt` |
| **教学知识点推断** | 从教材章节信息推断学生应掌握的知识点 | `textbook_kg.txt` |

## 目录结构

```
edukg/core/llm_inference/
├── __init__.py              # 模块导出
├── config.py                # 配置（模型名称、阈值、批量参数）
├── prompt_templates.py      # Prompt 加载和格式化
├── dual_model_voter.py      # 双模型投票核心逻辑
├── prerequisite_inferer.py  # 前置关系推断器
├── README.md                # 本文档
└── prompts/                 # 提示词文件目录
    ├── prerequisite.txt     # 前置关系推断提示词
    ├── kp_match.txt         # 知识点匹配提示词
    ├── definition_deps.txt  # 定义依赖抽取提示词
    └── textbook_kg.txt      # 教学知识点推断提示词
```

## 核心组件

### 1. DualModelVoter - 双模型投票器

```python
from edukg.core.llm_inference import DualModelVoter

# 创建投票器（支持依赖注入）
voter = DualModelVoter(
    primary_model="glm-4-flash",    # 免费
    secondary_model="deepseek-chat", # DeepSeek-V3
    llm_gateway=None                 # 可注入 LLM Gateway
)

# 执行投票
result = await voter.vote(prompt)

if result['consensus']:
    print(f"投票结果: {result['result']}")
    print(f"置信度: {result['confidence']}")
```

**投票规则**：
| 两模型结果 | 置信度 | 状态 |
|------------|--------|------|
| 一致 | ≥ 0.8 | 接受（PREREQUISITE） |
| 一致 | < 0.8 | 候选（PREREQUISITE_CANDIDATE） |
| 不一致 | - | 不采纳 |

### 2. PromptLoader - 提示词加载器

```python
from edukg.core.llm_inference.prompt_templates import PromptLoader

loader = PromptLoader()

# 从文件加载提示词
prompt = loader.load("prerequisite")  # 加载 prompts/prerequisite.txt

# 格式化提示词
formatted = loader.format(prompt, kp_a_name="加法", kp_a_description="...")

# 后续可扩展从 MySQL 加载
# loader._load_from_db("prerequisite")
```

### 3. 格式化函数

```python
from edukg.core.llm_inference.prompt_templates import (
    format_prerequisite_prompt,
    format_kp_match_prompt,
    format_definition_deps_prompt,
    format_textbook_kg_prompt,
)

# 前置关系推断
prompt = format_prerequisite_prompt(
    kp_a_name="加法",
    kp_a_description="把两个数合并成一个数的运算",
    kp_b_name="乘法",
    kp_b_description="求几个相同加数的和的简便运算"
)

# 教学知识点推断
prompt = format_textbook_kg_prompt(
    stage="小学",
    grade="三年级",
    semester="上册",
    chapter_name="时、分、秒",
    section_name="秒的认识",
    existing_kps=[]  # 为空则完全推断
)
```

## 提示词说明

### prerequisite.txt - 前置关系推断

区分两种关系：
- **PREREQUISITE**：学习依赖（不学A就学不懂B）
- **TEACHES_BEFORE**：教学顺序（教材先教A后教B，但学B不一定需要先学A）

输出格式：
```json
{
    "is_prerequisite": true,
    "confidence": 0.95,
    "reason": "乘法是加法的简便运算，必须先理解加法"
}
```

### kp_match.txt - 知识点匹配

判断教材知识点与知识图谱知识点是否为同一概念。

输出格式：
```json
{
    "is_match": true,
    "confidence": 0.90,
    "reason": "两者描述的是同一数学概念"
}
```

### textbook_kg.txt - 教学知识点推断

从教材章节信息推断学生应掌握的知识点。

输入：学段、年级、册次、章节名称、小节名称、已有知识点
输出：
```json
{
    "knowledge_points": ["正数的概念", "负数的概念", "0的意义"],
    "confidence": 0.95,
    "notes": "依据人教版七年级上册1.1节标准教学内容"
}
```

## 配置说明

`config.py` 主要配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `PRIMARY_MODEL` | `glm-4-flash` | 主模型（免费） |
| `SECONDARY_MODEL` | `deepseek-chat` | 副模型（DeepSeek-V3） |
| `CONFIDENCE_THRESHOLD_HIGH` | `0.8` | 高置信度阈值 |
| `CONFIDENCE_THRESHOLD_LOW` | `0.6` | 低置信度阈值 |
| `BATCH_SIZE` | `10` | 批处理大小 |
| `RATE_LIMIT_DELAY` | `1.0` | API 调用间隔（秒） |

## LLM 任务特性

所有 LLM 推断任务**必须支持断点续传**：

| 特性 | 说明 | 实现方式 |
|------|------|---------|
| **TaskState** | 任务状态管理 | 记录已处理的知识点对 |
| **CachedLLM** | LLM 调用缓存 | 相同输入复用结果 |
| **ProcessLock** | 进程锁保护 | 防止多进程冲突 |
| **进度保存** | 每 N 个保存一次 | 避免全部丢失 |
| **断点加载** | 启动时加载进度 | `--resume` 参数 |

## 使用场景

### 场景 1：前置关系推断（kg-math-prerequisite-inference）

```python
from edukg.core.llm_inference import PrerequisiteInferer

inferer = PrerequisiteInferer()

# 从 Neo4j 加载知识点
concepts = load_concepts_from_neo4j()

# 批量推断前置关系
results = await inferer.infer_batch(
    concepts,
    resume=True  # 支持断点续传
)

# 保存结果
inferer.save_results(results, "llm_prereq.json")
```

### 场景 2：教学知识点推断（kg-math-complete-graph）

```python
from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_textbook_kg_prompt

voter = DualModelVoter()

# 推断教学知识点
prompt = format_textbook_kg_prompt(
    stage="小学",
    grade="三年级",
    semester="上册",
    chapter_name="时、分、秒",
    section_name="秒的认识",
    existing_kps=[]
)

result = await voter.vote(prompt)
knowledge_points = result['result']['knowledge_points']
```

### 场景 3：知识图谱匹配（kg-math-complete-graph）

```python
from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt

voter = DualModelVoter()

# 匹配教材知识点到知识图谱
prompt = format_kp_match_prompt(
    textbook_kp_name="正数和负数的概念",
    textbook_kp_description="大于0的数叫正数，小于0的数叫负数",
    kg_kp_name="正数",
    kg_kp_description="数学概念..."
)

result = await voter.vote(prompt)
if result['consensus'] and result['result']['is_match']:
    print(f"匹配成功，置信度: {result['confidence']}")
```

## 命令行工具

### infer_prerequisites.py

```bash
# 估算成本
python edukg/scripts/kg_inference/infer_prerequisites.py --dry-run

# 执行推断（支持断点续传）
python edukg/scripts/kg_inference/infer_prerequisites.py --resume

# 查看统计
python edukg/scripts/kg_inference/infer_prerequisites.py --stats
```

### match_textbook_kp.py

```bash
# 执行匹配
python edukg/scripts/kg_data/match_textbook_kp.py --resume

# 查看统计
python edukg/scripts/kg_data/match_textbook_kp.py --stats
```

## 输出文件

输出目录：`edukg/data/edukg/math/6_推理结果/output/`

| 文件 | 说明 |
|------|------|
| `teaches_before.json` | 教材教学顺序关系 |
| `definition_deps.json` | 定义依赖关系 |
| `llm_prereq.json` | LLM 推断的前置关系 |
| `final_prereq.json` | 融合后的最终前置关系 |
| `matches_kg_relations.json` | 教材知识点匹配关系 |
| `validation_report.json` | DAG 验证报告 |

## 成本估算

基于 1,295 个知识点：

| 项目 | 数量 |
|------|------|
| 知识点对 | ~2,590 |
| LLM 调用 | ~5,180（双模型） |
| GLM-4-flash | 免费 |
| DeepSeek-V3 | 约 0.003 元 |
| **总计** | **< 0.01 元** |

## 依赖

| 模块 | 说明 |
|------|------|
| `ai-edu-ai-service/core/gateway/factory.py` | LLM Gateway |
| `edukg/core/neo4j/client.py` | Neo4j 客户端 |
| `edukg/core/llmTaskLock` | 断点续传支持 |
| `langchain-core` | LangChain 消息类型 |

## 测试

```bash
# 运行单元测试
pytest tests/core/llm_inference/ -v

# 测试覆盖：投票逻辑、推断逻辑、DAG 验证、提示词格式化
```

## 相关 Change

| Change | 描述 |
|--------|------|
| `kg-math-prerequisite-inference` | 前置关系推断 |
| `kg-math-complete-graph` | 教材数据导入 + 知识点匹配 |