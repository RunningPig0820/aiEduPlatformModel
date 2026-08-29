# 演进与未来

> summary: 演进与未来
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-ui-backend-15-演进与未来.md
> 类别：未来演进

---

> 检索摘要：知识图谱页面化后续怎么演进？多学科什么时候扩展？权限控制/管理员审核/班级老师学生关联等后续规划是什么？

## 当前阶段范围

当前阶段先做数学学科人教版教材知识点同步 + 导航 + 知识体系，后续扩展多学科。前端为独立部署，尚无 SPA 项目，页面由前端同学按 API 文档开发。

## 后续阶段规划（来自 Non-Goals 的延期项）

- 管理员审核/重跑功能：列为后续阶段，本期不做
- 权限控制：当前不实现，后续组织结构/权限模块补充
- AI 批改/举一反三：不属于本后端方案，由 Python 服务负责

## 全局存储与关联演进

知识点全局存储，后续班级/老师/学生通过关联表引用知识点 ID（当前预留关联引用字段）。状态机 merged 时，运营可通过 merged_to_uri 做进度迁移。

> 证据：详见 `2.OpenSpec design 决策/design-backend-2026-06-03-knowledge-graph-ui.md`（§Context 数据范围、§Non-Goals、§D2 状态机）
