# 知识点学段/章节归属反查（mastery stage 字段）

> summary: MasteryItemDTO 增 stage+章节归属，kp_uri 反查 kp→section→chapter→textbook 链取学段，批量 LEFT JOIN 反查避免 N+1，学段比年级更稳。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D13-知识点学段-章节归属反查-mastery-stage字段.md
> 类别：数据关联

> 检索摘要：MasteryItemDTO 增 stage+章节归属，kp_uri 反查 kp→section→chapter→textbook 链取学段，批量 LEFT JOIN 反查避免 N+1，学段比年级更稳。

**决策**：`MasteryItemDTO` 增加 `stage`（primary/middle/high）+ 可选 `chapterLabel`/`sectionLabel`。反查链路沿用现有 `getKnowledgePointDetail` 的 kp→section→chapter 两级，再延伸一跳 chapter→textbook 取 stage：

```
kp_uri → t_kg_section_kp → t_kg_chapter_section → t_kg_textbook_chapter → t_kg_textbook(stage)
```

**批量反查**：新增值对象 `KgKpPlacement`（kpUri/stage/chapterLabel/sectionLabel）+ `KgKnowledgePointRepository.findPlacementByUris(List<String>)`，Mapper 一条 LEFT JOIN SQL 批量反查（`getStudentMastery` 一次返回多 kp，避免 N+1）。一个 kp 挂多个 section 时取首个非空 stage（跨教材同 kp 罕见，取先收录）。

**理由**：学生掌握点天然跨年级（三年级可问初中内容），"按年级框定范围"的前提不成立；学段是更宽更稳的分组粒度。`stage` 已在 `KgTextbook.stage`（与 `KgStageEnum` code 对齐），零 schema 变更，纯反查。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D13 知识点学段/章节归属反查（mastery stage 字段））
