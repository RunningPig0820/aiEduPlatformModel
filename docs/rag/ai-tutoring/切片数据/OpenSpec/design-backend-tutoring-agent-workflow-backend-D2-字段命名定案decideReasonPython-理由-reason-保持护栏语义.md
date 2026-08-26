# design-backend-tutoring-agent-workflow-backend

> summary: 面试问答：后端D2阶段字段命名定案，新增decideReason字段
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: D2. 字段命名定案：`decideReason`（Python 理由）+ `reason` 保持护栏语义
> 模块: ai-tutoring ｜ 节: design-backend-tutoring-agent-workflow-backend
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-backend-tutoring-agent-workflow-backend-D2-字段命名定案decideReasonPython-理由-reason-保持护栏语义.md
> 类别：架构设计

---

### D2. 字段命名定案：`decideReason`（Python 理由）+ `reason` 保持护栏语义

**不重定义 `SseMetaDTO.reason`**（护栏拒绝原因不变），**新增 `decideReason`** 承载 Python 决策自由文本：

- `buildMeta` **无条件** `meta.setDecideReason(action.getReason())`（null ok）。
- `reason`（护栏拒绝原因 `answerCountInsufficient` / `roundLimitExceeded` / `safetyFlagHit`）语义与既有行为不变，仍仅拒绝时 set。
- `denied`（原始请求 type，如 reveal）保留——前端 D3 表用 `denied` + `answerRequestCount` 确定性推导"护栏拦"主文案，不依赖两个 reason 字段。

选择 `decideReason` 而非方案 A（`reason`=Python 理由 + `deniedReason`=护栏原因）：
- **additive，零重定义**：`reason` 既有语义不动，无回归面；方案 A 需改 `reason` 语义（虽当前前端不读，但语义切换有隐性契约变动）。
- **命名更准**：该字段就是 decide 步输出的理由 → `decideReason` 直白；`reason`（护栏 code）与 `decideReason`（Python 文本）语义清晰可分。
- **实现与前端已提交**：前端 change 文档与 Java 实现已按 `decideReason` 落地（测试 42/42 绿），保持现状零代码重做。

**同一轮对比（第 1 次要答案被护栏拦）：**

```
本变更: type="approach" denied="reveal" reason="answerCountInsufficient" decideReason="学生第 1 次明确要求答案"
方案 A: type="approach" denied="reveal" reason="学生第 1 次明确要求答案" deniedReason="answerCountInsufficient"
```

- 两条方案主文案相同（`denied`+计数推导），差别只在 hover 数据源字段名。
- 本变更 `decideReason` = Python 自由文本（hover），`reason` = 护栏 code（前端不消费，调试用）。
