# 数据来源与数据治理

> summary: 数据来源与数据治理
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-data-research-02-数据来源与数据治理.md
> 类别：数据关联

---

> 检索摘要：图谱数据从哪来、可信度如何、如何整合与更新？主数据源为 EduKG TTL 知识点实例(v0.1)+relations 关系(v0.1)，main.ttl(v3.0)提供教材/年级信息，entities 实体链接，好未来数据作层级参考；权威 TTL 冻结只读、仅增量补充题目-知识点关联。

**数据源分析（状态：）**

| 数据源 | 版本 | 内容 | 用途 |
|---|---|---|---|
| ttl/*.ttl | v0.1 | 知识点实例 | 主要数据源 |
| relations/*.ttl | v0.1 | 知识点关系 | 关联/分类关系 |
| main.ttl | v3.0 | 教材出处 | 年级/教材信息（已拆分为 split/main-{subject}.ttl） |
| entities/*.json | v0.1 | 实体列表 | 实体链接 |
| 好未来数据 | - | 小学数学 | 📖 层级参考 |

**整合策略（状态：）**——五步流程：
Step 1 以 ttl/*.ttl 为主数据源 → Step 2 通过标签匹配 split/main-{subject}.ttl 获取教材信息（如数学使用 main-math.ttl）→ Step 3 从教材信息推断年级 → Step 4 导入 relations/*.ttl 的关联关系 → Step 5 构建 PREREQUISITE 关系。

**跨源映射表（状态：构想）**：未来可能引入外部数据（如好未来数据），需建立跨源映射避免 URI 变化导致关系失效。以 SQLite 表 `kp_source_mapping` 保存标准 URI 与外部 ID 映射，字段：canonical_uri（标准 URI，内部唯一标识）、external_id（外部数据源 ID）、source_name（数据源名称 edukg/haoweilai/etc）、confidence（匹配置信度，默认 1.0），UNIQUE(canonical_uri, external_id, source_name)。

**数据更新机制（Demo 阶段，状态：）**
- 基准数据：edukg 静态权威库，知识点**永久冻结只读**
- 维护规则：仅增量补充「题目-知识点」关联，不修改基准知识点
- 版本管理：CSV 文件命名区分（如 knowledge_points_v1.csv）
- 长期维护：Demo 阶段不考虑，正式迭代再设计

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§三 数据来源与整合策略、§2.2.1 跨源映射表、§十二 数据更新机制）
