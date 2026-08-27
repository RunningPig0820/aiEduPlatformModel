# 知识点池获取与keyword搜索兜底

> summary: 知识点池按学段取 label（findLabelsByStage），knowledge-points 支持 keyword 搜索，空候选时学生手动确认知识点。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D9-知识点池获取与keyword搜索兜底.md
> 类别：架构设计

---

### D9：知识点池获取 + keyword 搜索兜底

> 检索摘要：知识点池按学段取 label（findLabelsByStage），knowledge-points 支持 keyword 搜索，空候选时学生手动确认知识点。

- `KgKnowledgePointRepository.findLabelsByStage(stage)`：按学段取知识点 label 池（D8 ③ 用，全量教材知识点）。
- `POST /api/kg/knowledge-points` 支持 `keyword` 参数：`WHERE label LIKE CONCAT('%', #{keyword}, '%')`（在 stage 过滤内）→ 前端 `KpSearchSelector` 空候选时手动搜教材知识点确认（选中 kpLabel 走 vote，镜像天然可 vote）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D9）｜ 完善文档 07-题目知识点与图谱关联.md
