# 引导问题体系
> summary: 引导问题体系
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-frontend-11-引导问题体系.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端引导 chips 怎么接入？进入时 GET /guide 展示开始引导 chips、每轮 done.suggestions 渲染结束建议 chips 可点再问；guide 端点依赖后端 F-M6。

### Goals（引导相关条目）
> 检索摘要：Goals 中的引导 chips：引用面板/成本面板/引导 chips/澄清点选 为前端目标清单项。

- 引用面板（灰显 → quotedKeys 高亮）、成本面板（本轮 + 会话累计）、引导 chips、澄清点选

### D2: 助手面板形态（引导入口）
> 检索摘要：面板对话区含结束建议 chips 与开始引导 chips(GET /guide) 入口，位于整体面板形态图内。

面板整体形态图中引导相关布局：

```
│ 对话区: 用户 / AI 流式回答 / 结束建议chips      │
│ 开始引导 chips(GET /guide) · 结束对话按钮       │
```

- 对话区下方有**开始引导 chips（GET /guide）**入口与"结束对话"按钮；每轮回答尾部渲染**结束建议 chips**（可点再问重走链路）。

### 风险与权衡（引导相关条目）
> 检索摘要：F-M6 引导端点依赖后端：guide 端点待后端建，F-M6 引导待 guide 端点就绪。

- **后端端点未建（依赖后端 M3–M7）** → 联调时 Java 仅有 `/ask` + `/ask/sync`；`source`(F-M3)/`guide`(F-M6)/`eval/report`(F-M5)/`close`·`turns`(F-M7) 端点待后端建。F-M6 引导待 guide 端点。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-frontend-rag-assistant-frontend.md`（§Goals/Non-Goals §D2 助手面板形态 §Risks/Trade-offs）
