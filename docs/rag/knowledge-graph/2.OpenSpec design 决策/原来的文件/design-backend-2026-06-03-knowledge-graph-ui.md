## Context

知识图谱数据已存储在远程 Neo4j，包含人教版 K-12 数学教材的完整结构。当前 Java 后端无 Neo4j 集成代码。前端为独立部署（尚无 SPA 项目）。

**决策方向**：用户选择方案 B — 将 Neo4j 知识点数据同步到 MySQL，前端 SPA 读取 MySQL。知识点全局存储，后续班级/老师/学生通过关联表引用知识点ID。

**数据范围**：当前阶段先做数学学科的人教版教材知识点同步 + 导航 + 知识体系。后续扩展多学科。

**前端职责**：后端负责 API 设计和接口实现，前端页面由前端同学根据 API 文档开发。

## Goals / Non-Goals

**Goals:**
- 提供一键同步按钮，将 Neo4j 的 Textbook/Chapter/Section/TextbookKP 同步到 MySQL
- 提供知识点导航 API，支持学科→年级→教材→章节→小节→知识点 6 级逐级浏览
- 提供年级知识体系 API，构建某年级完整知识结构
- 知识点详情接口返回 2 层父级（小节 + 章节），不过度展示
- 知识点全局存储，预留关联引用字段供后续班级/老师/学生关联
- 提供前端可参考的 API 接口定义和 DTO 结构
- 同步对话框提供学科/年级/学段下拉选择器（从 t_kg_textbook 聚合查询），避免手动输入

**Non-Goals:**
- 不做前端页面开发（后端提供 API，前端自行开发）
- 不做 Neo4j 实时查询（同步到 MySQL 后，前端只读 MySQL）
- 不做知识图谱关系可视化（Statement/Class/PART_OF 等复杂关系）— **知识点图谱关系已通过 Neo4j 查询**
- 不做管理员审核/重跑功能（后续阶段）
- 不做 AI 批改/举一反三（Python 服务负责）
- 当前不实现权限控制（后续组织结构/权限模块补充）

## Decisions

### 1. 数据方案：Neo4j → MySQL 同步 + Neo4j 关系查询

**决策**: MySQL 存储核心节点属性和层级关系（用于导航和进度统计），图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等）不同步到 MySQL，后续通过 Neo4j 直接查询。

**MySQL 表设计**:

```sql
-- ============================================
-- 节点主表（存储属性，URI 作为唯一标识）
-- ============================================

-- 教材表
CREATE TABLE t_kg_textbook (
    uri VARCHAR(255) NOT NULL PRIMARY KEY,     -- URI 作为主键
    label VARCHAR(128) NOT NULL,                -- 教材名称
    grade VARCHAR(32) NOT NULL,                 -- 年级
    phase VARCHAR(16) NOT NULL,                 -- 学段: primary/middle/high
    subject VARCHAR(16) DEFAULT 'math',         -- 学科
    status VARCHAR(16) DEFAULT 'active',        -- 状态: active/deleted/merged
    merged_to_uri VARCHAR(512),                 -- 被合并时指向新URI
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 章节表
CREATE TABLE t_kg_chapter (
    uri VARCHAR(255) NOT NULL PRIMARY KEY,      -- URI 作为主键
    label VARCHAR(128) NOT NULL,
    topic VARCHAR(64),                          -- 专题
    status VARCHAR(16) DEFAULT 'active',
    merged_to_uri VARCHAR(512),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 小节表
CREATE TABLE t_kg_section (
    uri VARCHAR(255) NOT NULL PRIMARY KEY,      -- URI 作为主键
    label VARCHAR(128) NOT NULL,
    status VARCHAR(16) DEFAULT 'active',
    merged_to_uri VARCHAR(512),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 知识点表（全局存储，后续班级/学生通过关联表引用）
CREATE TABLE t_kg_knowledge_point (
    uri VARCHAR(255) NOT NULL PRIMARY KEY,      -- URI 作为主键
    label VARCHAR(256) NOT NULL,
    difficulty VARCHAR(16),                     -- easy/medium/hard
    importance VARCHAR(16),                     -- low/medium/high
    cognitive_level VARCHAR(32),                -- 记忆/理解/应用/分析
    status VARCHAR(16) DEFAULT 'active',        -- 状态: active/deleted/merged
    merged_to_uri VARCHAR(512),                 -- 被合并时指向新URI
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- 层级关系表（固定结构，用于快速导航和进度统计）
-- ============================================

-- 教材 -> 章节
CREATE TABLE t_kg_textbook_chapter (
    textbook_uri VARCHAR(255) NOT NULL,
    chapter_uri   VARCHAR(255) NOT NULL,
    order_index   INT DEFAULT 0,
    PRIMARY KEY (textbook_uri, chapter_uri),
    FOREIGN KEY (textbook_uri) REFERENCES t_kg_textbook(uri),
    FOREIGN KEY (chapter_uri) REFERENCES t_kg_chapter(uri)
);

-- 章节 -> 小节
CREATE TABLE t_kg_chapter_section (
    chapter_uri VARCHAR(255) NOT NULL,
    section_uri VARCHAR(255) NOT NULL,
    order_index INT DEFAULT 0,
    PRIMARY KEY (chapter_uri, section_uri),
    FOREIGN KEY (chapter_uri) REFERENCES t_kg_chapter(uri),
    FOREIGN KEY (section_uri) REFERENCES t_kg_section(uri)
);

-- 小节 -> 知识点 (TextbookKP)
CREATE TABLE t_kg_section_kp (
    section_uri VARCHAR(255) NOT NULL,
    kp_uri      VARCHAR(255) NOT NULL,
    order_index INT DEFAULT 0,
    PRIMARY KEY (section_uri, kp_uri),
    FOREIGN KEY (section_uri) REFERENCES t_kg_section(uri),
    FOREIGN KEY (kp_uri) REFERENCES t_kg_knowledge_point(uri)
);

-- ============================================
-- 同步记录表
-- ============================================
CREATE TABLE t_kg_sync_record (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    sync_type VARCHAR(16) NOT NULL,             -- full (按需触发)
    scope JSON,                                 -- 同步范围：{"subject":"math","grade":"一年级"} 等
    status VARCHAR(16) NOT NULL,                -- running/success/failed
    inserted_count INT DEFAULT 0,               -- 新增数量
    updated_count INT DEFAULT 0,                -- 更新数量
    status_changed_count INT DEFAULT 0,         -- 状态变更数量（deleted/merged）
    reconciliation_status VARCHAR(16),          -- matched/mismatched（对账结果）
    reconciliation_details JSON,                -- 对账详情：neo4j counts vs mysql counts
    error_message TEXT,
    details JSON,                               -- 同步明细：各阶段耗时、异常 URI 列表
    started_at DATETIME,
    finished_at DATETIME,
    created_by BIGINT                           -- 操作人
);
```

### 2. 同步策略：按需触发 + UPSERT + 状态机

**决策**: 同步为**手动按需触发**（非实时监听/CDC），同步粒度为教材-学科-年级维度。采用 UPSERT 策略（按 URI 判断），同步节点属性和层级关系。图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等）**不同步到 MySQL**，后续通过 Neo4j 直接查询。

**同步范围**:

| 同步对象 | MySQL 操作 | Neo4j 角色 |
|---------|-----------|-----------|
| 节点属性 | 根据 URI UPSERT 到主表 | 数据源 |
| 层级关系 | 同步 CONTAINS/IN_UNIT 到关联表（含 order_index） | 数据源 |
| 图谱关系 | **不同步** | **直接提供查询服务** |

**同步流程**:
1. 获取同步锁（MySQL 应用层锁或 Redis 分布式锁）
2. 后端连接 Neo4j，依次查询：
   - 节点：Textbook → Chapter → Section → TextbookKP
   - 层级关系：CONTAINS（含 order_index）, IN_UNIT
3. **URI 校验**：拦截非法 URI（空值、重复、格式异常），记录到同步日志并跳过
4. 按 URI 执行 UPSERT（**整个同步流程在一个大事务内**）：
   - 节点主表：INSERT ... ON DUPLICATE KEY UPDATE
   - 关联表：先清空该层级的全部关联，再重新 INSERT（含 order_index 从 Neo4j 关系属性读取）
5. 标记 MySQL 中有但 Neo4j 中无的记录为 `status = 'deleted'`（知识点表还需设置 `merged_to_uri` 如已知合并目标）
6. **对账校验**：同步完成后，对比 MySQL 与 Neo4j 的节点数/关联数，不一致则记录警告
7. 记录同步结果到 `t_kg_sync_record`（含 reconciliation_status 字段）
8. 释放同步锁，返回同步统计

**同步失败处理**: 同步失败后用户可重新触发，从头执行。因为 UPSERT 是幂等的且整个流程在事务内，失败会自动回滚，不会导致重复数据或半清空状态。后续全量同步也是基于教材-学科-年级维度生成多个同步任务。

**同步事务原子性保证**:
- 整个同步流程（节点 UPSERT + 关联表重建 + 状态变更 + 对账校验）在一个 Spring `@Transactional` 事务内执行
- 关联表重建期间，前端导航查询看到的是旧数据（事务未提交前不可见），避免「空目录」问题
- 同步完成后事务提交，前端立即看到新数据，无中间状态

**支持定向同步参数**:
- `POST /api/kg/sync/full` 支持可选参数：`subject`（学科）、`phase`（学段）、`grade`（年级）、`textbookUri`（指定教材）
- 不传参数则全量同步所有数据
- 同步记录表 `t_kg_sync_record` 增加 `scope` 字段（JSON 格式）记录本次同步范围

**状态机说明**:

| 状态 | 含义 | 查询行为 |
|------|------|---------|
| `active` | 正常节点 | 正常展示 |
| `deleted` | Neo4j 中已删除 | 导航/知识体系查询中过滤掉（视为不存在），但进度记录不受影响（进度查询不过滤 deleted） |
| `merged` | 被合并到其他知识点 | 同上过滤，运营可通过 `merged_to_uri` 做进度迁移 |

**查询过滤**: 所有导航/知识体系查询自动加 `WHERE status = 'active'`。**进度查询例外**：学习进度查询需要包含已删除知识点的历史记录，通过 `isDeprecated` 字段标识，前端展示为"已归档"。

### 3. 并发控制：MySQL 同步锁

**决策**: 同步接口使用 MySQL 应用层行锁（`SELECT ... FOR UPDATE` on a sync lock row）或 Redis 分布式锁，确保同一时间只有一个同步任务执行。

### 4. 数据库索引设计

**决策**: 除主键外，对常用查询字段添加索引。

```sql
-- 教材表查询索引
CREATE INDEX idx_kg_textbook_grade ON t_kg_textbook(grade);
CREATE INDEX idx_kg_textbook_subject ON t_kg_textbook(subject);
CREATE INDEX idx_kg_textbook_phase ON t_kg_textbook(phase);

-- 章节表查询索引
CREATE INDEX idx_kg_chapter_topic ON t_kg_chapter(topic);

-- 知识点表查询索引
CREATE INDEX idx_kg_kp_status ON t_kg_knowledge_point(status);
CREATE INDEX idx_kg_kp_label ON t_kg_knowledge_point(label(100));
CREATE INDEX idx_kg_kp_difficulty ON t_kg_knowledge_point(difficulty);
CREATE INDEX idx_kg_kp_merged ON t_kg_knowledge_point(merged_to_uri(100));

-- 层级关联表排序索引
CREATE INDEX idx_kg_tc_chapter ON t_kg_textbook_chapter(chapter_uri, order_index);
CREATE INDEX idx_kg_cs_section ON t_kg_chapter_section(section_uri, order_index);
CREATE INDEX idx_kg_sk_kp ON t_kg_section_kp(kp_uri, order_index);

-- 同步记录表查询索引
CREATE INDEX idx_kg_sync_status ON t_kg_sync_record(status, started_at);
```

### 5. Neo4j 查询降级与缓存

**决策**: 图谱关系查询（直接查 Neo4j）在应用层加短期缓存（Redis，TTL 5 分钟），并提供降级机制。

- **缓存策略**: 查询结果存入 Redis，key 为 `kg:neo4j:{uri}:{query_type}`，TTL = 300s
- **降级机制**: Neo4j 不可用时，返回空关联数据，不抛异常。前端通过 `neo4jAvailable: false` 标识隐藏图谱模块
- **批量查询**: 提供 `/api/kg/concepts/batch-relations` 接口，一次性传入多个 URI，避免 N+1 查询
- **健康检查**: `/api/kg/neo4j/health` 接口定期检查 Neo4j 连接状态

### 6. 知识点唯一标识：URI

**决策**: MySQL 所有主表以 `uri` 作为主键（而非自增 ID）。URI 是 Neo4j 中的天然唯一标识（如 `http://edukg.org/knowledge/3.1/textbook/一年级上册`），同步时直接按 URI UPSERT，下游引用也使用 URI 而非 MySQL 自增 ID。

**URI 校验规则**:
- 同步时检查 URI 非空、格式以 `http://edukg.org/knowledge/` 开头
- 同批次同步中检测 URI 重复，记录到同步日志并跳过
- URI 生成后永不修改（若需修改走合并流程）

### 7. Domain 层建模：URI 主键 Entity + 关联表

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

### 8. 分层架构对齐现有模式

与现有代码保持一致：
- **Domain**: Entity + Value Object + Repository 接口
- **Infrastructure**: JPA Repository 实现 + Neo4j Sync Service（同步时使用）+ Neo4j Relation Query Service（图谱关系查询）
- **Application**: `KgSyncAppService`（同步）+ `KgNavigationAppService`（导航查询）
- **Interface**: `KnowledgeGraphController`（`/api/kg/**`）

### 9. 前端对接：API 接口定义 + DTO 结构

**决策**: 后端负责 API 设计和 DTO 定义，前端同学根据 API 文档开发页面。

**知识点详情 DTO**：
```java
// 知识点详情 DTO - 包含 2 层父级
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

### 10. 同步下拉选项数据源（枚举 + MySQL 混合）

**决策**: 同步对话框中的下拉选项数据源采用**枚举 + MySQL 混合**方式：
- **学科列表**：在 Java 枚举类中定义（固定值，学科种类不会变化）
- **学段列表**：在 Java 枚举类中定义（小学/初中/高中，固定三个值）
- **教材列表**：在 Java 枚举类中定义（固定值，教材相对固定）
- **年级列表**：从 MySQL `t_kg_textbook` 表 `DISTINCT grade` 查询（年级取决于实际同步的教材数据）

**枚举类定义**：
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

**同步前置要求**:
- 首次使用时，管理员需**先执行一次全量同步**，将 Neo4j 中的教材数据同步到 `t_kg_textbook`
- 全量同步完成后，年级下拉选项才有数据
- 学科和学段下拉选项始终可用（来自枚举）

**下拉选项 API**:
- `GET /api/kg/dimensions/subjects` → 从 `KgSubjectEnum` 枚举读取，按 orderIndex 排序
- `GET /api/kg/dimensions/grades` → `SELECT DISTINCT grade FROM t_kg_textbook WHERE status='active' ORDER BY grade`
- `GET /api/kg/dimensions/phases` → 从 `KgPhaseEnum` 枚举读取，按 orderIndex 排序
- `GET /api/kg/dimensions/textbooks` → 从 `KgTextbookEnum` 枚举读取，按 orderIndex 排序

### 11. 导航树扩展为 6 级

**决策**: 导航树从原有的 4 级（教材→章节→小节→知识点）扩展为 6 级（学科→年级→教材→章节→小节→知识点）。

**新增接口**:
- `GET /api/kg/subjects` — 根节点：学科列表（从 t_kg_textbook DISTINCT subject 查询）
- `GET /api/kg/subjects/{subject}/grades` — 学科下的年级列表（从 t_kg_textbook WHERE subject=? DISTINCT grade 查询）
- `GET /api/kg/grades/{grade}/textbooks` — 年级下的教材列表（从 t_kg_textbook WHERE grade=? 查询）

**数据来源**: 所有导航树层级数据均来自 `t_kg_textbook` 表聚合查询，不依赖额外配置表。

**前端导航流程**:
```
1. 用户进入知识图谱页面
2. GET /subjects -> 显示学科列表（数学、语文、英语...）
3. 用户点击"数学" -> GET /subjects/数学/grades -> 显示年级列表
4. 用户点击"一年级" -> GET /grades/一年级/textbooks -> 显示教材列表
5. 用户点击教材 -> GET /textbooks/{uri}/chapters -> 展开章节
6. 逐级展开 -> 小节 -> 知识点
7. 用户点击知识点 -> GET /knowledge-points/{uri}/graph -> 展示图谱关系
```

### 12. API 设计

```
# 同步相关（当前阶段不实现权限控制）
POST /api/kg/sync/full              - 触发全量同步（可选参数：subject/phase/grade/textbookUri）
GET  /api/kg/sync/status            - 查询同步状态
GET  /api/kg/sync/records           - 同步历史记录

# 维度配置（下拉选择器数据源，从枚举+MySQL读取，无需登录）
GET  /api/kg/dimensions/subjects    - 获取学科列表（前端下拉用，枚举）
GET  /api/kg/dimensions/grades      - 获取年级列表（前端下拉用，MySQL）
GET  /api/kg/dimensions/phases      - 获取学段列表（前端下拉用，枚举）
GET  /api/kg/dimensions/textbooks   - 获取教材列表（前端下拉用，枚举）

# 导航相关（扩展为 6 级：学科→年级→教材→章节→小节→知识点）
GET  /api/kg/subjects               - 获取学科列表（导航树根节点）
GET  /api/kg/subjects/{subject}/grades - 获取学科下的年级列表
GET  /api/kg/grades/{grade}/textbooks  - 获取年级下的教材列表
GET  /api/kg/textbooks              - 获取教材列表
GET  /api/kg/textbooks/{uri}        - 获取教材详情
GET  /api/kg/textbooks/{uri}/chapters - 获取教材章节树
GET  /api/kg/sections/{uri}/points    - 获取小节知识点
GET  /api/kg/knowledge-points/{uri}   - 获取知识点详情（含 2 层父级）
GET  /api/kg/knowledge-points/{uri}/graph - 获取知识点图谱关系

# 知识体系（无需登录）
GET  /api/kg/system/grade/{grade}    - 获取某年级完整知识体系
GET  /api/kg/system/stats/{grade}    - 获取年级知识点统计

# 图谱关系查询（直接查 Neo4j，用于后续扩展）
GET  /api/kg/concepts/{uri}/relations - 获取概念关联图（Neo4j，含 Redis 缓存）
GET  /api/kg/concepts/batch-relations - 批量获取概念关联图（避免 N+1）
GET  /api/kg/knowledge-points/{uri}/path - 获取知识点到概念的完整路径（Neo4j）
GET  /api/kg/neo4j/health            - Neo4j 健康检查
```

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| Neo4j 同步耗时长 | UPSERT 批量写入 + 事务控制，6,757 节点预计 < 10s |
| 同步并发冲突 | MySQL 应用层锁或 Redis 分布式锁，同一时间仅一个同步任务 |
| 同步期间前端看到空数据 | 整个同步在事务内执行，提交前前端看不到中间状态 |
| 状态变更导致 MySQL 数据膨胀 | `status='deleted'` 的数据定期清理（需确认无下游引用后物理删除） |
| 层级关联表重建开销 | 关联表无状态，每次同步先 DELETE 再 INSERT，简单可靠 |
| 图谱关系与 MySQL 不同步 | 层级关系同步到 MySQL，图谱关系实时查 Neo4j，不存在不一致 |
| 前端跨域问题 | Java 后端配置 CORS |
| Neo4j 服务不可用 | Redis 缓存 + 降级机制，Neo4j 不可用时返回空关联，不影响 MySQL 导航 |
| URI 脏数据写入 | 同步时校验 URI 格式/非空/唯一性，异常记录日志并跳过 |
| 同步后数据不一致 | 对账校验：同步完成自动对比 MySQL vs Neo4j 节点数/关联数 |
| URI 主键性能问题 | 当前 < 1 万节点，VARCHAR(255) 主键完全可行；若后续暴涨可引入整型代理键 |
| 首次使用下拉选项为空 | 提示用户先执行全量同步，t_kg_textbook 有数据后下拉选项自动可用 |

## Open Questions

<!-- 已确认，无遗留问题 -->
