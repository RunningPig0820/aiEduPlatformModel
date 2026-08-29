# 页面锚定与检索范围
> summary: 页面锚定与检索范围
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-frontend-04-页面锚定与检索范围.md
> 类别：架构设计

---

> 检索摘要（业务向）：前端每次 ask 携带的 currentProject 页面锚点怎么定？页面 pageCode → 模块 id 映射、模块 id 闭集（ai-tutoring/knowledge-graph/question-analysis/rag-system）怎么设计？按页独立会话（换页清空重介绍）如何规避跨页上下文矛盾？

### D3: currentProject 来源（页面 → 模块锚点，定稿 4 id 闭集）
> 检索摘要：每次 ask 携带 currentProject 模块 id（页面 pageCode 映射），模块 id 闭集定稿：ai-tutoring/knowledge-graph/question-analysis/rag-system，clarify 候选为字符串 id 数组。

每次 `ask` 携带 `currentProject`（camelCase），由 **当前页面 pageCode → 模块 id** 映射（`src/constants/pageModuleMap.js`）。模块 id 闭集三端定稿（**rag-system，弃 rag-project；question-analysis，弃 question-type**）：

| 模块 id | 业务模块 | 语料 |
|---|---|---|
| ai-tutoring | AI答疑 | 已有 234 块 |
| knowledge-graph | 知识图谱 | 未切片 |
| question-analysis | 题型分析 | 未切片 |
| rag-system | RAG 项目 | 未切片（9 节待跑） |

页面映射（pageCode → id）：STUDENT_AI_QA→ai-tutoring（**保留**，供后续 AI答疑页挂面板）/ STUDENT_KNOWLEDGE_GRAPH·STUDENT_REPORT_MAP→knowledge-graph / 题型掌握·题型分析→question-analysis / 缺省→rag-system（全局）。

`pageModuleMap` 同时维护 **id→中文 label**：clarify `candidates` 为**字符串 id 数组**，前端渲染候选 chips 用 label；点选以 **id** 作为 `currentProject` 重发；**未知 id 显示原文兜底**。

### D11: 按页会话（换页独立刷新，演示定稿）
> 检索摘要：面板按 pageCode 重挂载每页独立会话，换页清空会话/token/流水线重新介绍当前页，规避 LLM 上下文猜错模块与用户所在页的矛盾。

面板按 pageCode 重挂载（`key={pageCode}`），**每页独立会话**：换页即清空对话框/sessionId/token/流水线，重新介绍当前页功能；在途 SSE 随卸载 cleanup 取消，不串页。**页面是唯一权威上下文，不做跨页历史维护**——规避"继续介绍指哪模块 / LLM 上下文猜错模块 vs 用户所在页"的矛盾。

**后端/模型可选对齐（不做不阻塞，前端已按页独立）**：
- Python `resolve_clarify`：`current_project` 为有效页面锚点且问题含指代词（"这个/当前/继续"）→ 直接按页面默认回答，不触发 clarify（"这个功能是干什么的"在知识图谱页 → 直接介绍知识图谱）。
- Java：换页可调 `close` 结算旧会话（F-M7 端点就绪后）；每页新 sessionId 天然独立记账。

### 风险与权衡（页面锚定相关条目）
> 检索摘要：页面→模块映射不完整风险：缺省 rag-system 全局兜底，后续页面对应语料入库即自动可答。

- **页面→模块映射不完整** → 缺省 rag-system 兜底；后续页面对应语料入库即自动可答。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-frontend-rag-assistant-frontend.md`（§D3 currentProject 来源 §D11 按页会话 §Risks/Trade-offs）
