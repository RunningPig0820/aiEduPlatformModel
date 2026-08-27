# 验证方案（续）
> summary: 验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-验证方案-3.md
> 类别：开发难点

---

### 九、验证方案（Demo 阶段务实策略）（续）

> 检索摘要：验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。

#### 9.4.3 分层抽样评估（新增）
> 检索摘要：分层抽样评估按关系来源分组抽样，评估标准分定义依赖/LLM推理/教材顺序三类的强合理/弱合理/不合理判定。

问题：按来源分层抽样，便于定位问题。
def stratified_sampling(prerequisites: list, sample_size: int = 100) -> dict:
    """
    按来源分层抽样
    """
    from collections import defaultdict
    import random

    # 按来源分组
    by_source = defaultdict(list)
    for rel in prerequisites:
        by_source[rel['source']].append(rel)

    # 分层抽样
    samples = {}
    for source, rels in by_source.items():
        n = max(1, int(sample_size * len(rels) / len(prerequisites)))
        samples[source] = random.sample(rels, min(n, len(rels)))

    return samples

评估标准细化：
类型	强合理	弱合理	不合理
定义依赖	定义中直接包含前置概念	定义中间接引用	匹配错误
LLM 推理	明确必须掌握	有较强辅助作用	完全无关
教材顺序	-	仅时间依赖	-

#### 9.4.4 置信度校准（新增）
> 检索摘要：置信度校准对比模型置信度与专家打分计算校准因子，识别模型过自信/保守，便于后续阈值调整。

问题：模型输出置信度可能过于乐观或保守。
def calibrate_confidence(prerequisites: list, expert_scores: dict) -> dict:
    """
    置信度校准：对比专家打分
    expert_scores: {relation_id: expert_score_0_to_1}
    返回: {'overconfident': bool, 'calibration_factor': float}
    """
    model_scores = []
    human_scores = []

    for rel in prerequisites:
        if rel['id'] in expert_scores:
            model_scores.append(rel['confidence'])
            human_scores.append(expert_scores[rel['id']])

    if not model_scores:
        return {'overconfident': None, 'calibration_factor': 1.0}

    # 计算平均偏差
    avg_model = sum(model_scores) / len(model_scores)
    avg_human = sum(human_scores) / len(human_scores)

    calibration_factor = avg_human / avg_model if avg_model > 0 else 1.0

    return {
        'overconfident': avg_model > avg_human,
        'calibration_factor': calibration_factor,
        'avg_model_confidence': avg_model,
        'avg_human_score': avg_human
    }

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§九、验证方案（Demo 阶段务实策略）（续））
