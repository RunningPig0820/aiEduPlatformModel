# 实施步骤
> summary: 实施分四阶段：数据清洗整合→导入Neo4j→构建前置依赖(含LLM跨章节补充+人工审核接口)→验证优化，按学科逐个处理。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-实施步骤.md
> 类别：操作流程

---

### 六、实施步骤
> 检索摘要：实施分四阶段：数据清洗整合→导入Neo4j→构建前置依赖(含LLM跨章节补充+人工审核接口)→验证优化，按学科逐个处理。

阶段一：数据清洗与整合 (按学科逐个处理)
Step 1.1: 选择学科 (从数学开始)
Step 1.2: 解析 ttl/math.ttl → 提取知识点
Step 1.3: 解析 relations/math_relations.ttl → 提取关系
Step 1.4: 匹配 split/main-math.ttl → 获取教材信息
Step 1.5: 推断年级信息
Step 1.6: 数据验证

阶段二：导入 Neo4j
Step 2.1: 创建学科/学段/年级节点
Step 2.2: 创建教材/章节节点
Step 2.3: 创建知识点节点
Step 2.4: 创建分类关系 (BELONGS_TO)
Step 2.5: 创建关联关系 (RELATED_TO)

阶段三：构建前置依赖
Step 3.1: 基于教材章节顺序生成基础依赖
Step 3.2: 调用 LLM 补充跨章节依赖
Step 3.3: 合并去重，按置信度排序
Step 3.4: 导入 Neo4j (PREREQUISITE 关系)
Step 3.5: 提供人工审核接口

阶段四：验证与优化
Step 4.1: 抽查前置关系的合理性
Step 4.2: 验证学习路径的正确性
Step 4.3: 收集反馈，持续优化

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§六、实施步骤）
