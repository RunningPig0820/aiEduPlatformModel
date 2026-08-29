# 导航、下拉与缓存降级

> summary: 导航、下拉与缓存降级
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-10-页面化与服务化-4.md
> 类别：操作流程

---

> 检索摘要：导航树怎么从 4 级扩成 6 级？学科/年级/教材下拉选项从哪来？年级知识体系接口怎么设计？图谱关系查询 Neo4j 不可用时怎么降级？

## 导航树扩展为 6 级（D11）

导航树从原有的 4 级（教材→章节→小节→知识点）扩展为 6 级（学科→年级→教材→章节→小节→知识点）。

新增接口：
- GET /api/kg/subjects — 根节点：学科列表（从 t_kg_textbook DISTINCT subject 查询）
- GET /api/kg/subjects/{subject}/grades — 学科下的年级列表（从 t_kg_textbook WHERE subject=? DISTINCT grade 查询）
- GET /api/kg/grades/{grade}/textbooks — 年级下的教材列表（从 t_kg_textbook WHERE grade=? 查询）

数据来源：所有导航树层级数据均来自 t_kg_textbook 表聚合查询，不依赖额外配置表。

前端导航流程：
1. 用户进入知识图谱页面
2. GET /subjects 显示学科列表（数学、语文、英语等）
3. 用户点击「数学」→ GET /subjects/数学/grades 显示年级列表
4. 用户点击「一年级」→ GET /grades/一年级/textbooks 显示教材列表
5. 用户点击教材 → GET /textbooks/{uri}/chapters 展开章节
6. 逐级展开 → 小节 → 知识点
7. 用户点击知识点 → GET /knowledge-points/{uri}/graph 展示图谱关系

## 同步下拉选项数据源：枚举 + MySQL 混合（D10）

同步对话框中的下拉选项数据源采用枚举 + MySQL 混合方式：
- 学科列表：Java 枚举类定义（固定值，学科种类不会变化）
- 学段列表：Java 枚举类定义（小学/初中/高中，固定三个值）
- 教材列表：Java 枚举类定义（固定值，教材相对固定）
- 年级列表：从 MySQL t_kg_textbook 表 DISTINCT grade 查询（年级取决于实际同步的教材数据）

枚举类定义：
```java
// 学科枚举
public enum KgSubjectEnum {
    MATH("math", "数学", 1),
    CHINESE("chinese", "语文", 2),
    ENGLISH("english", "英语", 3),
    PHYSICS("physics", "物理", 4),
    CHEMISTRY("chemistry", "化学", 5),
    BIOLOGY("biology", "生物", 6);
    private final String code;
    private final String label;
    private final int orderIndex;
}

// 学段枚举
public enum KgPhaseEnum {
    PRIMARY("primary", "小学", 1),
    MIDDLE("middle", "初中", 2),
    HIGH("high", "高中", 3);
    private final String code;
    private final String label;
    private final int orderIndex;
}

// 教材枚举
public enum KgTextbookEnum {
    PEP_MATH_PRIMARY_G1("pep-math-primary-g1-v1", "人教版小学数学一年级上册", "math", "一年级", "primary", 1),
    BSV_MATH_PRIMARY_G1("bsv-math-primary-g1-v1", "北师大版小学数学一年级上册", "math", "一年级", "primary", 2);
    private final String uri;
    private final String label;
    private final String subject;
    private final String grade;
    private final String phase;
    private final int orderIndex;
}
```

同步前置要求：首次使用时，管理员需先执行一次全量同步，将 Neo4j 中的教材数据同步到 t_kg_textbook；全量同步完成后，年级下拉选项才有数据；学科和学段下拉选项始终可用（来自枚举）。

下拉选项 API：
- GET /api/kg/dimensions/subjects → 从 KgSubjectEnum 枚举读取，按 orderIndex 排序
- GET /api/kg/dimensions/grades → SELECT DISTINCT grade FROM t_kg_textbook WHERE status='active' ORDER BY grade
- GET /api/kg/dimensions/phases → 从 KgPhaseEnum 枚举读取，按 orderIndex 排序
- GET /api/kg/dimensions/textbooks → 从 KgTextbookEnum 枚举读取，按 orderIndex 排序

## 知识体系 API（D12.4）

- GET /api/kg/system/grade/{grade} 获取某年级完整知识体系
- GET /api/kg/system/stats/{grade} 获取年级知识点统计

## Neo4j 查询降级与缓存（D5）

图谱关系查询（直接查 Neo4j）在应用层加短期缓存（Redis，TTL 5 分钟），并提供降级机制。
- 缓存策略：查询结果存入 Redis，key 为 kg:neo4j:{uri}:{query_type}，TTL = 300s
- 降级机制：Neo4j 不可用时，返回空关联数据，不抛异常。前端通过 neo4jAvailable: false 标识隐藏图谱模块
- 批量查询：提供 /api/kg/concepts/batch-relations 接口，一次性传入多个 URI，避免 N+1 查询
- 健康检查：/api/kg/neo4j/health 接口定期检查 Neo4j 连接状态

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D11、§D10、§D12.4、§D5）
