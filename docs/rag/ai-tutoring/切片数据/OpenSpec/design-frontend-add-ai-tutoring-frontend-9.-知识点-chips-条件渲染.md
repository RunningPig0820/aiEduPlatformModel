# design-frontend-add-ai-tutoring-frontend

> summary: 讲AI答疑知识点chips的条件渲染规则
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 9. 知识点 chips 条件渲染
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend

---

### 9. 知识点 chips 条件渲染

- 数据源:`meta.eval.masterySignals`(后端已放行的信号,含 kpLabel + signal)
- 规则(压噪):仅在 `done` 后更新;最多 4 个 chip,超出折叠 `+N`;信号 → 颜色(mastered 绿 / practicing 黄 / struggling 红)
- **无信号数组 → 整行不渲染**。纯字符串渲染,零前端知识点模块依赖;后端 Python 未排期、暂不发信号时自动隐藏,不阻塞
- 与未来学生端知识图谱页共享 `GET /students/{id}/mastery`,但本页不实现叠加
