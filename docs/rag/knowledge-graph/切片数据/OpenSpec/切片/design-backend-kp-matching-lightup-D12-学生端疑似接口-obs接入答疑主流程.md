# 学生端疑似接口 + obs 接入答疑主流程

> summary: 新增 GET /api/students/{id}/pending-kps 返回该生 PENDING/WEAK 观测；applyMasteryAndErrors 升级调用 resolve 使 obs 接入答疑主流程、年级锚生效。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-backend-kp-matching-lightup-D12-学生端疑似接口-obs接入答疑主流程.md
> 类别：操作流程

> 检索摘要：新增 GET /api/students/{id}/pending-kps 返回该生 PENDING/WEAK 观测；applyMasteryAndErrors 升级调用 resolve 使 obs 接入答疑主流程、年级锚生效。

**决策**：补两个前端对接暴露的缺口：

1. **学生端疑似接口** `GET /api/students/{id}/pending-kps`：返回该生 `status=PENDING/WEAK` 的派生观测（学生权限，studentId 必须等于会话 userId）。学生端"待确认清单"（疑似薄弱点）的数据源。
2. **obs 接入答疑主流程**：`applyMasteryAndErrors` 升级为调用 `resolve(label, session.getStudentId())`（替代 `resolveLabelToUri` 的 default 兼容路径），使解析产生 obs、年级锚生效；掌握度写入同步取 status/confidence（不再硬编码 RESOLVED）。

**理由**：前端对接暴露两个断层——(a) `getMastery` 硬编码 RESOLVED，学生拿不到自己的疑似点（现有 pending 接口是 ADMIN/TEACHER 专属且返回全体）；(b) 灰度遗留：`resolveLabelToUri` 传 null，obs 派生层未接进答疑主流程，题型库聚合/维护闭环无输入数据。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-matching-lightup.md`（§D12 学生端疑似接口 + obs 接入答疑主流程）
