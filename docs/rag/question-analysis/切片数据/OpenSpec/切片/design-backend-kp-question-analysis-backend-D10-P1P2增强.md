# P1P2增强

> summary: P1/P2 增强：聚合手动触发即时验证沉淀、管理端审核页（P2）后续。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-backend-kp-question-analysis-backend-D10-P1P2增强.md
> 类别：业务视角

---

### D10：P1/P2 增强（非本次必须）

> 检索摘要：P1/P2 增强：聚合手动触发即时验证沉淀、管理端审核页（P2）后续。

- **聚合手动触发**：`POST /api/kp/aggregation/run`（ADMIN）→ `aggregationService.aggregate()`。联调时即时验证题型库沉淀（现状凌晨 3:17 定时，看不到效果）。
- **管理端审核页面**（P2，独立功能点，后续）：学生题型 ↔ 年级知识点对照，LLM 批量分析关联 + 人工校准 → 喂题型库（`kp-pending-review`）。

> 证据：详见 `2.OpenSpec design 决策/design-backend-kp-question-analysis-backend.md`（§D10）｜ 完善文档 08-演进路线.md
