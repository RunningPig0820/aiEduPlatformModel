# D4：数据库索引设计

> summary: 决策：除主键外对grade/subject/phase/topic/status等常用查询字段加索引，层级关联表加排序索引。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-2026-06-03-knowledge-graph-ui-D4-数据库索引设计.md
> 类别：数据存储

> 检索摘要：决策：除主键外对grade/subject/phase/topic/status等常用查询字段加索引，层级关联表加排序索引。

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

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§D4：数据库索引设计）
