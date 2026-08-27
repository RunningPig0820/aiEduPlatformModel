# 题型库分页 + 关联知识点接口（题型分析）

> summary: 新增题型库分页 GET /api/kp/question-types 与题型关联知识点接口，kpLabel 从 kg 镜像反查不冗余存 name。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D15-题型库分页-关联知识点接口-题型分析.md
> 类别：数据关联

> 检索摘要：新增题型库分页 GET /api/kp/question-types 与题型关联知识点接口，kpLabel 从 kg 镜像反查不冗余存 name。

**决策**：新增两个接口：
- `GET /api/kp/question-types?page=1&size=20`：分页列题型（`id`/`topicLabel`/`status`/`hitCount` + `total`），`QuestionTypeRepository` 补 `findPage`。
- `GET /api/kp/question-types/{id}/knowledge-points`：该题型关联知识点（`QuestionTypeKpRepository.findByQuestionTypeId` 已有 + `kgKnowledgePointRepository.findByUris` 反查 kpLabel），返回 `kpUri`/`kpLabel`/`gradeRange`/`ratio`/`hitCount`。

**理由**：题型分析页需"题型库浏览 + 通过题型看关联知识点"。`QuestionType`/`QuestionTypeKp` 目前只有 `kp_uri` 无 name，`kpLabel` 从 kg 镜像反查（不冗余存 name，权威标签唯一来源 kg 镜像）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D15 题型库分页 + 关联知识点接口（题型分析））
