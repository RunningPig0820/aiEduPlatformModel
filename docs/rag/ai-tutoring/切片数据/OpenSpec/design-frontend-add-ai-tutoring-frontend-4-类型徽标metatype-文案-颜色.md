# design-frontend-add-ai-tutoring-frontend

> summary: 说明AI答疑中类型徽标的渲染规则与会话结束判定
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 4. 类型徽标(meta.type → 文案 + 颜色)
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-frontend-add-ai-tutoring-frontend-4-类型徽标metatype-文案-颜色.md
> 类别：业务流程

---

### 4. 类型徽标(meta.type → 文案 + 颜色)

| type | 徽标文案 | 样式 | 说明 |
|---|---|---|---|
| hint | 引导 | primary(绿系/主题色) | 常规引导 |
| approach | 思路 | info | 不给完整演算 |
| reveal | 答案 | **warning** | 完整答案,结束时提示"本次答疑已结束" |
| concept | 概念 | neutral | 概念讲解 |
| switch | 换题 | divider 提示,非气泡徽标 | 换题分隔条 |
| end | 总结 | success | 收尾总结 |

`denied` 场景:meta.type 已是降级后的 type(如 approach),前端按该 type 渲染即可,`denied` 字段仅作可选的一次性轻提示(如"已为你调整为先展示思路")。徽标**纯展示、不可点击**——避免学生对后端语义产生额外操作预期。

**会话结束判定(后端确认 2026-08-06)**:`meta.status` 或 `done.status` 为 **ARCHIVED 或 TERMINATED 均视为会话结束**——输入区禁用、可发起新会话,前端**不只认 TERMINATED**。终止路径(`TERMINATED` + `reply`,无 token、**无 done**)对发起与中途同样生效;实测:安全命中 → TERMINATED,无关/非数学 → ARCHIVED 收尾(B4:Python decide 对无关内容返回带 end_reason 的 end,属 Python 侧问题,前端需兼容)。
