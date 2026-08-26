# 坑档案

> summary: 解决AI步骤消息无换行的显示问题
> 权威度: 0.8 ｜ 来源: 坑档案 ｜ 锚点: F5. AI 步骤消息无换行
> 模块: ai-tutoring ｜ 节: 坑档案
> COS路径: ai-tutoring/rag-slices/坑档案/坑档案-F5-AI-步骤消息无换行.md
> 类别：开发难点

---

### F5. AI 步骤消息无换行
**1. 问题现象**：AI 输出的步骤列表挤成一行——流式期间有换行，done 后反而消失（会话 103 实测 5 步挤成一段）。

**2. 触发流程**：AI 输出「步骤1:…\n步骤2:…」用单个换行分隔。流式期间 `MessageBubble.jsx:83` 用 `whitespace-pre-wrap` 有换行；`done` 后切 `ReactMarkdown` 渲染。

**3. 根因分析**：markdown 软换行（单个 `\n`）**默认被折叠成空格** → `ReactMarkdown` 把多步骤挤成一段。流式/完成两种渲染方式行为不一致。

**4. 排查过程**：从"完成后步骤挤一行"反推 → 对比流式（pre-wrap 有换行）与完成（ReactMarkdown 折叠）→ 确认是 markdown 软换行折叠。

**5. 解决方案 & 改动点**：提交 `5d0808b`——给 `ReactMarkdown` 加 `remark-breaks` 插件，单换行渲染 `<br>`。AI 答疑 `MessageBubble.jsx:4,86-88` 与通用面板 `AIChatPanel.jsx`（3 处）同步加。依赖 `package.json` `"remark-breaks": "^4.0.0"`。

**6. 面试口述要点**：讲"**渲染层行为要跟流式预览一致**"——markdown 软换行折叠 vs pre-wrap 保留，导致完成态比流式难看。踩坑收获：**AI 输出里单换行是语义（步骤分隔），要显式保留**；remark-breaks 是低成本方案，关键是不让"完成态"比"流式态"退化。

---
