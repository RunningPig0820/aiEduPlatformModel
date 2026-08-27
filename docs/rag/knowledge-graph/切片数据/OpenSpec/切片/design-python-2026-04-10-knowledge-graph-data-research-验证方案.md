# 验证方案
> summary: 验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-验证方案.md
> 类别：开发难点

---

### 九、验证方案（Demo 阶段务实策略）
> 检索摘要：验证方案务实策略：自动验证(循环依赖/年级倒置惩罚)+抽样测试(≥70%准确率即可)，Demo 不做人工教师审核。

#### 9.1 验证方式
> 检索摘要：验证方式三种：自动验证(循环/年级倒置)、抽样测试(≥70%准确率)、人工审核(教师，Demo 不做)。

方式	说明	Demo 阶段策略
自动验证	循环依赖检测、年级倒置检测（按跨度惩罚）	数据导入前自动执行
抽样测试	随机抽取检查合理性	≥70% 准确率即可满足 demo
人工审核	教师审核	不做，无相关人员参与

### 9.2 置信度处理
> 检索摘要：置信度分流规则：<0.8 的 LLM 候选存 PREREQUISITE_CANDIDATE，定义依赖直接生成 PREREQUISITE，多模型一致且≥0.8 生成，年级倒置按跨度惩罚。

● 置信度 < 0.8 的 LLM 候选：存入 PREREQUISITE_CANDIDATE
● 定义依赖：直接生成 PREREQUISITE
● LLM 多模型投票一致 + 置信度 ≥0.8：生成 PREREQUISITE
● 新增：年级倒置按跨度惩罚置信度（智谱建议）

### 9.3 年级倒置的宽松处理（智谱建议）
> 检索摘要：年级倒置按跨度惩罚置信度：0-2级相邻跨年级×0.95、跨1学段×0.9、跨2学段×0.5、跨度异常×0.3降为候选。

问题：原方案将"高年级指向低年级"直接判定为异常。但在实际教学中，跨学段复习或螺旋式课程设计是合理的（如高二物理用到初三数学知识）。
改进方案：按年级跨度设置不同的置信度惩罚权重：
# 年级顺序映射
GRADE_ORDER = {
    "小学": {"一年级": 1, "二年级": 2, "三年级": 3, "四年级": 4, "五年级": 5, "六年级": 6},
    "初中": {"初一": 7, "初二": 8, "初三": 9},
    "高中": {"高一": 10, "高二": 11, "高三": 12},
}

def apply_grade_penalty(relation, from_kp, to_kp):
    """
    根据年级跨度惩罚置信度
    """
    from_order = get_grade_order(from_kp.grade, from_kp.stage)
    to_order = get_grade_order(to_kp.grade, to_kp.stage)

    if from_order is None or to_order is None:
        return relation  # 无法判断，保持原置信度

    span = from_order - to_order  # 前置知识的年级 - 目标知识的年级

    if span <= 0:
        # 前置年级 ≤ 目标年级：正常，不惩罚
        return relation

    # 年级倒置（前置知识年级更高）
    if span <= 2:
        # 同学段或相邻年级：合理（如高一数学 -> 初三数学基础）
        penalty = 0.95  # 置信度 * 0.95
        reason = "跨相邻年级，视为合理复习关联"
    elif span <= 3:
        # 跨 1 个学段（如高中->初中）：需确认
        penalty = 0.9
        reason = "跨学段关联，置信度降低"
    elif span <= 6:
        # 跨 2 个学段（如高中->小学）：可能错误
        penalty = 0.5
        reason = "跨多学段，存入 PREREQUISITE_CANDIDATE"
    else:
        # 跨度太大：几乎肯定错误
        penalty = 0.3
        reason = "年级跨度异常，存入 PREREQUISITE_CANDIDATE"

    relation['confidence'] *= penalty
    relation['grade_penalty_reason'] = reason

    # 置信度过低则降级为候选关系
    if relation['confidence'] < 0.6:
        relation['relation_type'] = 'PREREQUISITE_CANDIDATE'

    return relation

惩罚规则总结：
年级跨度	示例	置信度惩罚	处理方式
0-2（相邻）	高一→初三数学基础	×0.95	正常，保留 PREREQUISITE
3（跨1学段）	高二→初三	×0.9	合理但需确认
4-6（跨2学段）	高中→小学	×0.5	存入 PREREQUISITE_CANDIDATE
>6（跨度太大）	高三→小学一年级	×0.3	存入 PREREQUISITE_CANDIDATE

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§九、验证方案（Demo 阶段务实策略））
