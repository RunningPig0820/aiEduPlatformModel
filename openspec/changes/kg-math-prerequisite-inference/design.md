## Context

前置关系推断是知识图谱项目的**核心设计成本**部分。需要区分教学顺序（TEACHES_BEFORE）和学习依赖（PREREQUISITE），通过多证据融合生成高质量的前置关系数据。

当前状态：
- **知识点**: 已导入 4,490 个数学知识点
- **原生关系**: 已导入 RELATED_TO, SUB_CATEGORY
- **LLM Gateway**: 支持 GLM-4-flash（免费）和 DeepSeek（低成本）

设计约束：
- 区分教学顺序 vs 学习依赖
- 使用多模型投票提高准确率
- 保留低置信度关系作为候选

## Goals / Non-Goals

**Goals:**
- 基于教材章节顺序推断 TEACHES_BEFORE
- 从定义文本抽取定义依赖
- LLM 多模型投票推断 PREREQUISITE
- 融合多证据来源
- 导入 Neo4j 并验证 DAG 合规性

**Non-Goals:**
- 不处理其他学科（物理/化学等）
- 不做人工审核（Demo 阶段自动化）
- 不处理小学数据

## Decisions

### D1: TEACHES_BEFORE 推断策略

**决策**: 基于教材章节顺序生成 TEACHES_BEFORE

```python
# 章节内顺序
for chapter in chapters:
    for i, kp in enumerate(chapter.knowledge_points):
        if i > 0:
            teaches_before.append((kp.uri, chapter.knowledge_points[i-1].uri))
```

**理由**:
- 教材章节顺序代表教学安排
- 仅限章节内部，跨章节不推断（避免错误）

**替代方案**: 全教材顺序推断
- **缺点**: 教材顺序不代表跨章节的教学依赖

### D2: 定义依赖抽取策略

**决策**: 从知识点定义文本匹配其他知识点名称

```python
# 定义匹配规则
def extract_definition_deps(definition: str, kp_names: List[str]) -> List[str]:
    """从定义文本中匹配知识点名称"""
    deps = []
    for name in kp_names:
        if name in definition:
            deps.append(name)
    return deps
```

**理由**:
- 定义中出现其他知识点名称是强证据
- 例："一元二次方程的解法" → 包含"一元二次方程"

### D3: LLM Prompt 设计

**决策**: 设计区分教学顺序 vs 学习依赖的 prompt

```python
PROMPT_TEMPLATE = """
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
```

**理由**:
- 明确区分两种关系语义
- 要求解释原因，提高判断质量

### D4: 多模型投票机制

**决策**: 使用 GLM-4-flash + DeepSeek 两模型投票

```python
# 投票规则
def vote_prerequisite(glm_result, deepseek_result):
    """两模型投票"""
    if glm_result['is_prerequisite'] and deepseek_result['is_prerequisite']:
        # 两模型一致认为存在依赖
        confidence = min(glm_result['confidence'], deepseek_result['confidence'])
        if confidence >= 0.8:
            return ('PREREQUISITE', confidence)
        else:
            return ('PREREQUISITE_CANDIDATE', confidence)
    else:
        # 两模型不一致，暂不采纳
        return None
```

**理由**:
- 两模型一致提高准确率
- 低置信度关系保留为候选，待后续验证
- 降低错误率

### D5: LLM Gateway Scene 配置

**决策**: 新增 `prerequisite_inference` scene

```python
# config/model_config.py
SCENE_MODEL_MAPPING = {
    'prerequisite_inference': {
        'provider': 'zhipu',
        'model': 'glm-4-flash',  # 主模型
        'fallback': 'deepseek',   # 备用模型
        'temperature': 0.3,       # 低温度，提高一致性
    }
}
```

**理由**:
- glm-4-flash 免费，降低成本
- deepseek 作为备用和投票模型
- 低温度提高输出一致性

### D6: 成本控制策略

**决策**: 使用免费模型 + 批量处理

```python
# 成本估算
# glm-4-flash: 免费（智谱免费额度）
# deepseek: 约 0.001 元/千token

# 批量处理
BATCH_SIZE = 10  # 每批 10 个知识点对
TOTAL_CALLS = 4490 * 2 = 8980  # 两模型各调用一次

# 预估成本
# DeepSeek: 8980 * 100 tokens * 0.001/1000 ≈ 0.9 元
```

**理由**:
- 主要使用免费模型
- DeepSeek 成本极低（<1 元）

### D7: DAG 验证策略

**决策**: 导入后验证无环

```python
# DAG 验证
def validate_dag(driver):
    """验证 PREREQUISITE 关系无环"""
    with driver.session() as session:
        result = session.run("""
            MATCH (a:KnowledgePoint)-[:PREREQUISITE]->(b:KnowledgePoint)
            MATCH path = (b)-[:PREREQUISITE*]->(a)
            RETURN count(path) as cycle_count
        """)
        cycle_count = result.single()['cycle_count']
        return cycle_count == 0
```

**理由**:
- DAG 是学习路径的前提条件
- 有环则学习路径计算错误

## Risks / Trade-offs

### Risk 1: LLM 推断准确率不足
**风险**: LLM 可能错误推断前置关系
**缓解**: 多模型投票 + 低温度 + 置信度阈值 + 候选关系保留

### Risk 2: 成本超预期
**风险**: 实际调用次数超过预期
**缓解**: 使用免费模型为主，批量处理，监控调用次数

### Risk 3: DAG 出现环
**风险**: 前置关系可能形成循环依赖
**缓解**: 导入前检查 + 导入后验证 + 发现环时报警

### Risk 4: 定义匹配噪音
**风险**: 定义文本可能包含无关知识点的名称
**缓解**: 仅匹配学科内知识点 + 设置最小匹配长度

## Migration Plan

**执行步骤**:
1. 运行 `infer_teaches_before.py` → 输出 `math_teaches_before.csv`
2. 运行 `extract_definition_deps.py` → 输出 `math_definition_deps.csv`
3. 运行 `infer_prerequisites_llm.py` → 输出 `math_llm_prereq.csv`
4. 运行 `fuse_prerequisites.py` → 输出 `math_final_prereq.csv`
5. 运行 `import_prereq_to_neo4j.py` → 导入 Neo4j
6. 运行 DAG 验证脚本 → 确认无环

**回滚策略**:
```cypher
// 删除所有推断关系
MATCH ()-[r:TEACHES_BEFORE]->() DELETE r
MATCH ()-[r:PREREQUISITE]->() DELETE r
MATCH ()-[r:PREREQUISITE_CANDIDATE]->() DELETE r
MATCH ()-[r:PREREQUISITE_ON]->() DELETE r
```

## Open Questions

无（设计已确定）