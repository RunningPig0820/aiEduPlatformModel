# D7：Domain 层建模：URI 主键 Entity + 关联表

> summary: 决策：Domain层用JPA Entity，主键为URI（String），Repository用Spring Data JPA+MyBatis-Plus混合，含关联表Entity。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D7-domain层建模-uri主键-entity-关联表.md
> 类别：架构设计

> 检索摘要：决策：Domain层用JPA Entity，主键为URI（String），Repository用Spring Data JPA+MyBatis-Plus混合，含关联表Entity。

**决策**: 同步后，知识点数据存储在 MySQL 中，Domain 层使用标准的 JPA Entity，主键为 URI（String 类型），Repository 使用 Spring Data JPA + MyBatis-Plus 混合。

**包结构**:
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

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D7：Domain 层建模：URI 主键 Entity + 关联表）
