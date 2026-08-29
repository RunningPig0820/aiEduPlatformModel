# 三端架构与分工

> summary: 三端架构与分工
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-11-三端架构与分工.md
> 类别：架构设计

---

> 检索摘要：知识图谱页面化的三端怎么分工？Java 后端负责什么、前端读什么、Neo4j 管什么？分层架构怎么对齐？/api/kg 接口契约和 DTO 长什么样？

## 三端职责分工（本文档口径）

- 数据源端 Neo4j：存完整知识图谱，提供图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等）直接查询服务
- Java 后端：负责将节点数据同步到 MySQL，并对外提供 /api/kg/** 接口（KnowledgeGraphController）与 DTO 定义
- 前端 SPA：只读 MySQL，页面由前端同学根据后端 API 文档开发
- 分工边界（Non-Goals）：不做前端页面开发；不做 Neo4j 实时查询（同步到 MySQL 后前端只读 MySQL）；不做知识图谱关系可视化（复杂关系已通过 Neo4j 查询）；AI 批改/举一反三由 Python 服务负责

## 分层架构对齐现有模式（D8）

与现有代码保持一致：
- Domain：Entity + Value Object + Repository 接口
- Infrastructure：JPA Repository 实现 + Neo4j Sync Service（同步时使用）+ Neo4j Relation Query Service（图谱关系查询）
- Application：KgSyncAppService（同步）+ KgNavigationAppService（导航查询）
- Interface：KnowledgeGraphController（/api/kg/**）

## Domain 层建模：URI 主键 Entity + 关联表（D7）

同步后知识点数据存储在 MySQL 中，Domain 层使用标准的 JPA Entity，主键为 URI（String 类型），Repository 使用 Spring Data JPA + MyBatis-Plus 混合。

包结构：
```
domain/edukg/model/entity/
  ├── KgTextbook.java              -- 主键: uri (String)
  ├── KgChapter.java               -- 主键: uri (String)
  ├── KgSection.java               -- 主键: uri (String)
  ├── KgKnowledgePoint.java        -- 主键: uri (String)
  └── relation/                    -- 层级关系 Entity
      ├── KgTextbookChapter.java   -- 主键: (textbookUri, chapterUri)
      ├── KgChapterSection.java    -- 主键: (chapterUri, sectionUri)
      └── KgSectionKP.java         -- 主键: (sectionUri, kpUri)
domain/edukg/model/valueobject/
  ├── KgDifficulty.java
  ├── KgImportance.java
  ├── KgCognitiveLevel.java
  └── KgNodeStatus.java       -- 枚举: active/deleted/merged
domain/edukg/repository/
  ├── KgTextbookRepository.java
  ├── KgChapterRepository.java
  ├── KgSectionRepository.java
  ├── KgKnowledgePointRepository.java
  ├── KgTextbookChapterRepository.java
  ├── KgChapterSectionRepository.java
  └── KgSectionKPRepository.java
```

## 前端对接：API 接口定义 + DTO 结构（D9）

后端负责 API 设计和 DTO 定义，前端同学根据 API 文档开发页面。

知识点详情 DTO（含 2 层父级，不过度展示）：
```java
public class KgKnowledgePointDetailDTO {
    private String uri;           // URI 作为唯一标识
    private String label;
    private String difficulty;
    private String importance;
    private String cognitiveLevel;
    // 2 层父级，不过度展示
    private String sectionUri;
    private String sectionLabel;  // 直接父级：小节
    private String chapterUri;
    private String chapterLabel;  // 爷爷级：章节
}
```

## API 契约设计（D12.1 ~ D12.5）

同步相关（D12.1）：
- POST /api/kg/sync/full —— 触发全量同步（可选参数：subject/phase/grade/textbookUri）
- GET /api/kg/sync/status —— 查询同步状态
- GET /api/kg/sync/records —— 同步历史记录

维度配置（D12.2）：
- GET /api/kg/dimensions/subjects —— 学科列表（前端下拉用，枚举）
- GET /api/kg/dimensions/grades —— 年级列表（前端下拉用，MySQL）
- GET /api/kg/dimensions/phases —— 学段列表（前端下拉用，枚举）
- GET /api/kg/dimensions/textbooks —— 教材列表（前端下拉用，枚举）

导航相关（D12.3）：
- GET /api/kg/subjects —— 学科列表（导航树根节点）
- GET /api/kg/subjects/{subject}/grades —— 学科下的年级列表
- GET /api/kg/grades/{grade}/textbooks —— 年级下的教材列表
- GET /api/kg/textbooks —— 教材列表
- GET /api/kg/textbooks/{uri} —— 教材详情
- GET /api/kg/textbooks/{uri}/chapters —— 教材章节树
- GET /api/kg/sections/{uri}/points —— 小节知识点
- GET /api/kg/knowledge-points/{uri} —— 知识点详情（含 2 层父级）
- GET /api/kg/knowledge-points/{uri}/graph —— 知识点图谱关系

知识体系（D12.4）：
- GET /api/kg/system/grade/{grade} —— 某年级完整知识体系
- GET /api/kg/system/stats/{grade} —— 年级知识点统计

图谱关系查询（D12.5，直接查 Neo4j）：
- GET /api/kg/concepts/{uri}/relations —— 概念关联图（Neo4j，含 Redis 缓存）
- GET /api/kg/concepts/batch-relations —— 批量概念关联图（避免 N+1）
- GET /api/kg/knowledge-points/{uri}/path —— 知识点到概念的完整路径（Neo4j）
- GET /api/kg/neo4j/health —— Neo4j 健康检查

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D7 Domain 建模、§D8 分层架构、§D9 前端对接、§D12.1~D12.5 API 设计）
