# 数据来源与整合策略
> summary: 图谱数据源整合：ttl 知识点实例与 relations 关系为主数据源，main.ttl 提供教材/年级信息，好未来数据作层级参考。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-数据来源与整合策略.md
> 类别：数据关联

---

### 三、数据来源与整合策略（数据源分析）
> 检索摘要：图谱数据源整合：ttl 知识点实例与 relations 关系为主数据源，main.ttl 提供教材/年级信息，好未来数据作层级参考。

#### 3.1 数据源分析
> 检索摘要：数据源五类：ttl 知识点实例/relations 关系为主源，main.ttl 提供教材年级，entities 实体链接，好未来数据作层级参考。

数据源	版本	内容	用途
ttl/*.ttl	v0.1	知识点实例	主要数据源
relations/*.ttl	v0.1	知识点关系	关联/分类关系
main.ttl	v3.0	教材出处	年级/教材信息（已拆分为 split/main-{subject}.ttl）
entities/*.json	v0.1	实体列表	实体链接
好未来数据	-	小学数学	📖 层级参考

### 3.2 整合策略
> 检索摘要：整合流程五步：ttl主数据源→标签匹配 main 教材→推断年级→导入 relations 关联→构建 PREREQUISITE。

Step 1: 以 ttl/*.ttl 为主数据源
↓
Step 2: 通过标签匹配 split/main-{subject}.ttl 获取教材信息（如数学使用 main-math.ttl）
↓
Step 3: 从教材信息推断年级
↓
Step 4: 导入 relations/*.ttl 的关联关系
↓
Step 5: 构建 PREREQUISITE 关系

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§三、数据来源与整合策略（数据源分析））
