# 分学科处理策略
> summary: 学科分三类：强逻辑链学科(数理化生)建 PREREQUISITE，语言学科(英语)建语法词汇层级，主题关联学科(历史语文地理政治)建主题分类。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-分学科处理策略.md
> 类别：数据关联

---

### 八、分学科处理策略（学科类型划分）
> 检索摘要：学科分三类：强逻辑链学科(数理化生)建 PREREQUISITE，语言学科(英语)建语法词汇层级，主题关联学科(历史语文地理政治)建主题分类。

#### 8.1 学科类型划分
> 检索摘要：学科分三类：强逻辑链(数理化生)建 PREREQUISITE、语言(英语)建语法词汇层级、主题(史地政语)建主题分类，优先级 P1/P2/P3。

学科类型	学科	关系特点	处理策略	优先级
强逻辑链学科	数学、物理、化学、生物	前置关系明确，学习顺序固定	构建 PREREQUISITE 关系	P1
语言学科	英语	语法层级、词汇递进	构建语法/词汇层级	P2
主题关联学科	历史、语文、地理、政治	主题/时间关联，非学习依赖	构建主题分类关系	P3

### 8.2 处理顺序 (Phase by Phase)
> 检索摘要：处理顺序四阶段：Phase1数学(4490知识点/relateTo9870)验证设计，Phase2数理化生构建关系，Phase3英语语法层级，Phase4主题学科。

Phase 1: 数学 (有关系数据，验证设计)
         - 知识点数: 4,490
         - relateTo: 9,870 (可直接使用)
         - subCategory: 328 (层级关系)
         - 目标: 验证整体流程可行性

Phase 2: 物理、化学、生物 (强逻辑链，需构建关系)
         - 物理: 3,385 知识点
         - 化学: 5,718 知识点
         - 生物: 15,209 知识点
         - 目标: 使用 LLM 构建前置关系

Phase 3: 英语 (语法层级)
         - 英语: 5,107 知识点
         - 目标: 构建语法/词汇层级

Phase 4: 历史、语文、地理、政治 (主题关联)
         - 历史: 4,850 知识点
         - 语文: 8,041 知识点
         - 地理: 4,682 知识点
         - 政治: 5,309 知识点
         - 目标: 构建主题分类，不做前置依赖

### 8.3 前置关系构建方案（已确认：LLM 推理）
> 检索摘要：前置关系构建已确认为 LLM 推理：GLM-4-flash 免费主力、批大小50、temperature 0.3、置信度<0.7丢弃，relateTo 保留为 RELATED_TO。

模型选择: GLM-4-flash (免费，主力)
# LLM 推理配置
LLM_CONFIG = {
    "provider": "zhipu",
    "model": "glm-4-flash",  # 免费，主力
    "scene": "prerequisite_inference",
    "batch_size": 50,  # 每批处理50个知识点
    "temperature": 0.3,  # 降低随机性，提高一致性
}

调用方式: 复用现有 LLM Gateway，新增 prerequisite_inference scene
推理流程:
1. 按学科分组知识点
2. 按章节/主题分批 (每批 50 个)
3. 调用 LLM 分析前置关系
4. 输出带置信度的关系数据
5. 置信度 < 0.7 直接丢弃，不做人工审核

relateTo 数据处理:
● relateTo → RELATED_TO（知识点关联，必须保留）
● Demo 阶段不做 LLM 验证补充，核心闭环跑通后再优化

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§八、分学科处理策略（学科类型划分））
