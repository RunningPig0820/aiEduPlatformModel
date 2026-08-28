# 核心功能与白盒问答
> summary: 核心功能与白盒问答-2（引用/成本/澄清/非学生占位）
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-frontend-02-核心功能与白盒问答-2.md
> 类别：操作流程

---

> 检索摘要（业务向）：前端引用面板怎么灰显折叠、done 后 quotedKeys 命中块高亮展开、filePath 查看原文？成本面板本轮+会话累计怎么展示、"结束对话"怎么结算？澄清 chips 怎么点选重发、非学生占位怎么处理？

### D5: 引用面板（灰显 → 高亮）
> 检索摘要：rerank 到达即渲染引用块卡片灰显折叠，done 后 quotedKeys 命中块高亮展开，filePath 可点查看原文（GET source?path= 用 query 传参）。

`rerank` 事件到达即渲染块卡片（blockId/title/summary/filePath，**灰显折叠**，filePath 可点"查看原文"）；`done` 后 `quotedKeys` 命中的块**高亮展开**、未命中保持灰显折叠。`quotedKeys` 为空 → 展示 answer 自带标注，不额外提示。

**"查看原文" URL 定稿**：`GET /api/rag/assistant/source?path=<urlencoded>`（Java 网关代理透传 Python，STUDENT 角色门）。前端**拼 query 传参，不走 path**（file_path 含 `http://` 前缀，走 path 会被容器拒）。

### D6: 成本面板（本轮 + 会话累计）
> 检索摘要：置顶头部展示本场累计 token，done.tokensUsage 到达即更新；"结束对话"调 close 接口返回会话累计 token 与轮数。

- 置顶头部展示**本场累计 token**；每轮 `done.tokensUsage` 到后更新（`cacheHitTokens` 为估算值时标注"估算"）。
- "结束对话"调 `POST /sessions/{sessionId}/close`，返回会话累计 token + 轮数 → 展示"本次对话总消耗"。

### D7: 澄清交互（点选候选 → 重发原问 + currentProject）
> 检索摘要：clarify 事件渲染 ClarifyCard，candidates 为字符串 id 数组，点选候选=重发原问+currentProject=点选模块 id，后端以 currentProject 权威锚定。

`clarify` 事件到达 → 渲染 ClarifyCard：固定话术 + 候选 chips + default 提示。**candidates 为字符串 id 数组**（如 `["ai-tutoring","rag-system"]`）；前端用 `pageModuleMap` 的 id→中文 label 渲染 chips（未知 id 显示原文兜底）。**点选候选 = 重发原问 + `currentProject`=点选模块 id**（契约已冻结，**不是发裸功能名**）。后端 intent 以 currentProject 为权威锚点直接锚定；点选模块与会话锚点不同 → `switch` 事件照常触发（前端提示"已切换至 X"）。

### D8: 非学生占位
> 检索摘要：面板读取 auth 角色置顶展示，非 STUDENT 显示"当前非学生无法使用"占位，不发起 ask、不弹走页面，后端 403 兜底。

面板读取 auth 角色置顶展示；角色非 STUDENT → 面板内显示"**当前非学生无法使用**"占位，不发起 ask（后端 403 兜底）。不弹走页面、不硬报错。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-frontend-rag-assistant-frontend.md`（§D5 引用面板 §D6 成本面板 §D7 澄清交互 §D8 非学生占位）
