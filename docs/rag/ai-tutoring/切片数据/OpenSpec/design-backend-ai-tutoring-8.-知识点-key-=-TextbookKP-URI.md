# design-backend-ai-tutoring

> summary: 解决AI辅导后端知识点key采用TextbookKP URI的问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 8. 知识点 key = TextbookKP URI
> 模块: ai-tutoring ｜ 节: design-backend-ai-tutoring

---

### 8. 知识点 key = TextbookKP URI

（保留原决策）每个知识点的稳定 key 采用知识图谱 `TextbookKP` 节点的 **URI**。学生掌握度 `t_student_kp_mastery.kp_key` 存 URI。label→URI 解析（`TutoringKpResolver`，Java 侧）在 kg-sync 的 MySQL 镜像（`KgKnowledgePointPo`，subject=math）中解析：精确 → LIKE → 未命中（记日志 + 收尾标记"待收录"，不点亮）。解析失败不影响答疑主流程。
