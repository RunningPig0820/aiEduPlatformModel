# 同步表设计与 URI 主键

> summary: 同步表设计与 URI 主键
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-10-页面化与服务化-2.md
> 类别：操作流程

---

> 检索摘要：同步到 MySQL 的 8 张表长什么样？t_kg_textbook/t_kg_knowledge_point 等表结构是什么？为什么用 URI 做主键而不是自增 ID？URI 校验规则有哪些？

## 同步数据方案（D1）——MySQL 表设计

MySQL 存储核心节点属性和层级关系（用于导航和进度统计），图谱关系（MATCHES_KG/PART_OF/RELATED_TO 等）不同步到 MySQL，后续通过 Neo4j 直接查询。

```sql
-- 节点主表（存储属性，URI 作为唯一标识）

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

-- 层级关系表（固定结构，用于快速导航和进度统计）

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

-- 同步记录表
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

## 知识点唯一标识：URI（D6）

MySQL 所有主表以 uri 作为主键（而非自增 ID）。URI 是 Neo4j 中的天然唯一标识（如 http://edukg.org/knowledge/3.1/textbook/一年级上册），同步时直接按 URI UPSERT，下游引用也使用 URI 而非 MySQL 自增 ID。

URI 校验规则：
- 同步时检查 URI 非空、格式以 http://edukg.org/knowledge/ 开头
- 同批次同步中检测 URI 重复，记录到同步日志并跳过
- URI 生成后永不修改（若需修改走合并流程）

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D1 表设计、§D6）
