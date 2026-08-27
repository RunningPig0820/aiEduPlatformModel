# 掌握度接口改造 + 派生覆盖度接口

> summary: 拆两个接口：GET /api/students/{id}/mastery 返回题型掌握度明细，GET /api/students/{id}/kp-coverage 返回知识点派生覆盖度，归属属性移入覆盖度接口。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D19-掌握度接口改造-派生覆盖度接口.md
> 类别：操作流程

> 检索摘要：拆两个接口：GET /api/students/{id}/mastery 返回题型掌握度明细，GET /api/students/{id}/kp-coverage 返回知识点派生覆盖度，归属属性移入覆盖度接口。

**决策**：拆两个接口，对应前端「掌握度」（题型四类明细）与「知识点总览」（派生覆盖度着色）：

- ① **改造** `GET /api/students/{id}/mastery` → 返回题型掌握度 `items[] { topicKey, topicLabel, masteryLevel, status, confidence, updatedAt }`。
- ② **新增** `GET /api/students/{id}/kp-coverage` → 返回知识点派生覆盖度 `items[] { kpUri, kpLabel, coverage, masteryLevel, status, confidence, stage, chapterLabel, sectionLabel }`。
- ③ 已实现保留：`POST /api/kg/knowledge-points`（全量知识点分页）、`GET /api/kp/question-types`（题型库分页）、`GET /api/kp/question-types/{id}/knowledge-points`。

**理由**：题型掌握度与知识点覆盖度是两个不同粒度视图（一个按题型、一个按知识点），拆开各自清晰。`stage`/`chapterLabel`/`sectionLabel` 从 mastery 移入覆盖度接口（这些是知识点的归属属性，题型无归属语义）；`kpLabel` 反查沿用 kg 镜像（权威标签唯一来源）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D19 掌握度接口改造 + 派生覆盖度接口）
