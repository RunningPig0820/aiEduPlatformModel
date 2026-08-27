# 开放问题

> summary: 开放项已全部关闭：菜单/展示/确认归属/候选来源（方案A）/空候选路径（keyword 搜索）均已定。
> 权威度: 0.7
> 模块: question-analysis
> COS路径: rag-slices/question-analysis/OpenSpec/design-frontend-kp-question-analysis-开放问题.md
> 类别：未来演进

---

### 开放问题

> 检索摘要：开放项已全部关闭：菜单/展示/确认归属/候选来源（方案A）/空候选路径（keyword 搜索）均已定。

> 已关闭：
> - **菜单形态**：子菜单——智能练习（一级）→ 题型分析（二级），页面统一。
> - **结果展示**：先纯分析（题型 + 关联知识点清单）；掌握度标注预留（数据到位自然亮）。
> - **后端 analyze-question**：独立一次 LLM 题目理解调用（从 decide 拆出，非整个 decide），无状态可复用。
> - **学生确认归属**：个人观测（`student_vote`），喂聚合任务；全局审核（管理端）另开功能点。
> - **聚合整理**：已存在且消费 STUDENT_VOTE，本方案只加确认入口，不新设计。
> - **pending-kps 确认交互（方案 a/b）**：确认选 **方案 a**——待确认清单每条展开候选可「确认」（复用 vote 转正，接口不变），学生贴题时与事后清单里都能补，闭环完整。
> - **candidates 校验**：后端确认 candidates 已镜像校验（正常 vote 不 10003）。
> - **WEAK 语义**：后端确认 WEAK 也返回 PENDING（不再冒充 RESOLVED），前端 PENDING 分支需覆盖「有/无 candidates」。
> - **待确认清单候选来源（A/B）**：选 **方案 A**——`pending-kps` 不含 candidates，前端展开时复用 `resolveKp(topicLabel)` 现取；WEAK 项自带 kpLabel 直接可确认。后端加字段（方案 B）留后续。
> - **PENDING 空候选确认路径**：选「后端加搜索接口」——`POST /api/kg/knowledge-points` 加可选 `keyword`，前端空态提供「搜索知识点」选择器，选中镜像知识点 → vote（保证可 vote 不 10003）。

> 证据：详见 `2.OpenSpec design 决策/design-frontend-kp-question-analysis.md`（§开放问题）｜ 语雀-决策记录.md D16/D15
