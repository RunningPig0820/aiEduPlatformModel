# 待确认清单候选来源

> summary: 待确认清单候选来源=复用 resolveKp 现取（方案A 零后端改动），WEAK 项自带 kpLabel 直接确认。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-D7-待确认清单候选来源.md
> 类别：操作流程

---

### 决策 7：待确认清单候选来源 = 复用 `resolveKp` 现取（方案 A）

> 检索摘要：待确认清单候选来源=复用 resolveKp 现取（方案A 零后端改动），WEAK 项自带 kpLabel 直接确认。

`PendingKpAliasDTO` **不含 candidates 字段**（仅 id/topicLabel/confidence/status/kpUri/kpLabel/…）。8.2 待确认清单确认交互的候选来源决策：

- **方案 A（选定）**：前端展开待确认项时，纯 PENDING 项调 `POST /api/kp/resolve { label: topicLabel }` 现取 candidates（复用既有接口，零后端改动）；WEAK 项自带 kpLabel 直接可确认。
- 方案 B（不选）：后端给 pending-kps 每条补 candidates 字段（接口增强，可后续优化）。

理由：`resolveKp` 已通（澄清卡同底层），先前端跑通闭环；后端加字段是低价值优化，等确认频率高时再做。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§决策 7）
