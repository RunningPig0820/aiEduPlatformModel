## Context

前置关系推断是知识图谱项目的**核心设计成本**部分。需要区分教学顺序（TEACHES_BEFORE）和学习依赖（PREREQUISITE），通过多证据融合生成高质量的前置关系数据。

当前状态：
- **知识点**: 已导入 EduKG 数据（Class 39, Concept 1,295, Statement 2,932）
- **原生关系**: 已导入 RELATED_TO 10,183, SUB_CLASS_OF 38, PART_OF 298, BELONGS_TO 619
- **LLM Gateway**: 支持 GLM-4-flash（免费）和 DeepSeek（低成本）

设计约束：
- 区分教学顺序 vs 学习依赖
- 使用多模型投票提高准确率
- 保留低置信度关系作为候选
- **核心代码放入 `edukg/core/llm_inference/`，scripts 只做命令行入口**

## Goals / Non-Goals

**Goals:**
- 基于教材章节顺序推断 TEACHES_BEFORE
- 从定义文本抽取定义依赖
- LLM 多模型投票推断 PREREQUISITE
- 融合多证据来源
- 输出 JSON 文件（手动验证后导入）

**Non-Goals:**
- 不处理其他学科（物理/化学等）
- 不做人工审核（Demo 阶段自动化）
- 不处理小学数据

## Decisions

### D1: 目录结构设计

**核心代码放入 `edukg/core/llm_inference/`**：

```
edukg/core/llm_inference/
├── __init__.py
├── dual_model_voter.py      # 双模型投票核心逻辑
├── prompt_templates.py       # LLM Prompt 模板
├── prerequisite_inferer.py   # 前置关系推断
├── definition_extractor.py   # 定义依赖抽取
├── teaches_before_inferer.py # 教学顺序推断
└── config.py                 # 配置（模型、阈值等）
```

**scripts 只做命令行入口**：

```
edukg/scripts/kg_inference/
├── infer_prerequisites.py    # 命令行入口
└── validate_dag.py           # DAG 验证入口
```

**理由**:
- 核心逻辑可复用（其他模块也可调用双模型投票）
- scripts 保持轻量，只做参数解析和调用
- 便于单元测试

### D2: 双模型投票模块 (dual_model_voter.py)

```python
"""
双模型投票核心模块
支持 GLM-4-flash + DeepSeek 两模型投票
"""

class DualModelVoter:
    """双模型投票器"""

    def __init__(self, primary_model: str = "glm-4-flash",
                 secondary_model: str = "deepseek-chat"):
        self.primary_model = primary_model
        self.secondary_model = secondary_model

    async def vote(self, prompt: str) -> Dict:
        """
        两模型投票

        Returns:
            {
                'consensus': bool,       # 是否达成一致
                'result': Any,           # 投票结果
                'confidence': float,     # 置信度
                'primary_response': ..., # 主模型响应
                'secondary_response': ... # 副模型响应
            }
        """

    def vote_prerequisite(self, glm_result, deepseek_result) -> Optional[Tuple]:
        """
        前置关系投票规则

        规则:
        - 两模型一致 + confidence >= 0.8 → PREREQUISITE
        - 两模型一致 + confidence < 0.8 → PREREQUISITE_CANDIDATE
        - 两模型不一致 → None（不采纳）
        """
```

### D3: LLM Prompt 模板 (prompt_templates.py)

```python
"""
LLM Prompt 模板集合
"""

PREREQUISITE_PROMPT = """
你是一位教育专家，请判断以下知识点之间的学习依赖关系。

**学习依赖**：不学A就学不懂B（核心前置）
**教学顺序**：教材先教A后教B，但学B不一定需要先学A

知识点A: {kp_a_name}
知识点A描述: {kp_a_description}

知识点B: {kp_b_name}
知识点B描述: {kp_b_description}

请回答：
1. 学习B是否需要先学习A？(是/否)
2. 置信度：(高/中/低)
3. 原因：(简短说明)

注意：区分"教学顺序"和"学习依赖"。
"""

# 用于 kg-math-complete-graph 的知识点匹配 Prompt
KP_MATCH_PROMPT = """
你是一位教育专家，请判断以下两个知识点是否表示同一个概念。

教材知识点: {textbook_kp_name}

知识图谱知识点: {kg_kp_name}
知识图谱描述: {kg_kp_description}

请回答：
1. 是否表示同一概念？(是/否)
2. 置信度：(0.0-1.0)
3. 原因：(简短说明)
"""
```

### D4: 前置关系推断模块 (prerequisite_inferer.py)

```python
"""
前置关系推断模块
"""

class PrerequisiteInferer:
    """前置关系推断器"""

    def __init__(self, voter: DualModelVoter):
        self.voter = voter

    async def infer_batch(self, kp_pairs: List[Dict]) -> List[Dict]:
        """
        批量推断前置关系

        Args:
            kp_pairs: [{'kp_a': {...}, 'kp_b': {...}}, ...]

        Returns:
            [{'kp_a_uri': ..., 'kp_b_uri': ..., 'relation': 'PREREQUISITE',
              'confidence': 0.9, 'source': 'llm_vote'}, ...]
        """

    def infer_from_textbook_order(self, chapters: List[Dict]) -> List[Dict]:
        """
        基于教材顺序推断 TEACHES_BEFORE

        规则: 仅限章节内部，跨章节不推断
        """

    def extract_from_definition(self, definition: str,
                                 kp_names: List[str]) -> List[str]:
        """
        从定义文本中匹配知识点名称
        """
```

### D5: 配置 (config.py)

```python
"""
推理配置
"""

# 模型配置
PRIMARY_MODEL = "glm-4-flash"      # 免费
SECONDARY_MODEL = "deepseek-chat"  # 低成本

# 投票阈值
CONFIDENCE_THRESHOLD_HIGH = 0.8    # >= 此值为 PREREQUISITE
CONFIDENCE_THRESHOLD_LOW = 0.6     # >= 此值为 CANDIDATE

# 批量处理
BATCH_SIZE = 10
RATE_LIMIT_DELAY = 1.0             # 每次调用后等待 1 秒

# 输出路径
OUTPUT_DIR = "edukg/data/edukg/math/6_推理结果/output/"
```

### D6: DAG 验证

**决策**: 输出 JSON 后验证无环

```python
def validate_dag(relations: List[Dict]) -> Tuple[bool, List[str]]:
    """
    验证 PREREQUISITE 关系无环

    Returns:
        (is_valid, cycles) - 是否有效，发现的环列表
    """
```

### D7: 输出文件结构

```
edukg/data/edukg/math/6_推理结果/output/
├── teaches_before.json       # TEACHES_BEFORE 关系
├── definition_deps.json      # 定义依赖
├── llm_prereq.json           # LLM 推断的前置关系
├── final_prereq.json         # 融合后的最终前置关系
└── validation_report.json    # DAG 验证报告
```

## Risks / Trade-offs

### Risk 1: LLM 推断准确率不足
**风险**: LLM 可能错误推断前置关系
**缓解**: 多模型投票 + 低温度 + 置信度阈值 + 候选关系保留

### Risk 2: 成本超预期
**风险**: 实际调用次数超过预期
**缓解**: 使用免费模型为主，批量处理，监控调用次数

### Risk 3: DAG 出现环
**风险**: 前置关系可能形成循环依赖
**缓解**: 输出后验证 + 发现环时报警

## Migration Plan

**执行步骤**:

1. **开发核心模块**:
   - 创建 `edukg/core/llm_inference/` 目录
   - 实现 `dual_model_voter.py`
   - 实现 `prompt_templates.py`
   - 实现 `prerequisite_inferer.py`

2. **开发命令行入口**:
   - 创建 `edukg/scripts/kg_inference/infer_prerequisites.py`

3. **运行推理**:
   - 运行命令行脚本
   - 输出 JSON 文件

4. **验证和导入**:
   - 运行 DAG 验证
   - 人工验证后手动导入 Neo4j

## Open Questions

无（设计已确定）