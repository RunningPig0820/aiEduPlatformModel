## Why

学生端"AI 答疑"是核心学习体验(引导式解答而非直接给答案)。后端 `ai-tutoring` 方案已定稿完整网关编排——decide → guard → generate 类型先行流式 SSE、拍题 OCR 前置、掌握度落库、会话生命周期——但前端 `/student/ai-qa` 目前只有路由常量和侧边栏菜单(status=pending),点击即 404。需要一个整页的 AI 智能体交互页面,消费该 SSE 协议并承载苏格拉底式引导的教学交互。

## What Changes

- 新增学生端整页答疑页面 `/student/ai-qa`(React,挂到 student 路由下,角色色 success)
- 新增 `tutoring` API 模块:
  - **SSE 类型先行消费**:处理 `meta`(type/roundCount/denied/eval/masterySignals)→ `token`(正文流)→ `done`(status/summary/endReason)三段事件;`denied` 场景无 token 流
  - REST:`POST /sessions`、`POST /sessions/{id}/messages`、`POST /sessions/{id}/request-answer`、`GET /sessions/{id}`、`POST /sessions/{id}/archive`、`GET /students/{id}/mastery`
  - OCR:`POST /tutoring/ocr`(multipart 上传)
- AI 回复按 action type 渲染类型徽标:`hint`引导 / `approach`思路 / `reveal`答案 / `concept`概念 / `switch`换题 / `end`总结,reveal 用警示色并在结束时明确提示
- 拍题 OCR 前置交互:上传照片 → 展示识别文本供确认/修改 → 确认后作为首条学生消息发起会话;OCR 失败走通用错误提示
- 当前题目置顶卡片(纯展示,= 首条用户消息,可折叠)
- "请求答案"按钮(第 1 次给思路 / 第 2 次给完整答案并结束会话),**第 2 次点击前弹确认**;轮次进度显示(≤20)
- 知识点 chips 行("本场涉及知识点",已掌握/练习中/待巩固),数据来自 `meta.eval.masterySignals`,**无信号时不渲染**
- 会话本地持久化(localStorage,DeepSeek 式断点恢复:刷新不丢对话)+ 服务端对账(`GET /sessions/{id}` 校正 counters/status),历史会话页面内轻量回看
- 收尾总结卡片:涉及知识点/薄弱点/轮次/掌握度,附"再来一题"(开新会话)入口
- 更新 `pageMeta` STUDENT_AI_QA:pending → active,features 去掉"语音问答"(不在后端范围);侧边栏菜单状态改 active,移除待开发包装

## Capabilities

### New Capabilities
- `ai-tutoring`: AI 答疑页面与交互——整页智能体聊天、类型徽标与护栏可见性、OCR 前置确认、当前题目卡片、轮次/请求答案、知识点 chips、收尾总结卡片、本地持久化断点恢复
- `ai-tutoring-api`: 答疑后端 API 客户端——SSE 类型先行(meta/token/done)消费、REST 会话接口、OCR 上传、断点对账

### Modified Capabilities
- `page-meta`: STUDENT_AI_QA 从 pending 转为 active,features/aiPrompts 对齐后端答疑能力范围

## Impact

- 新增页面:`ai-edu-front/src/pages/student/AiQa.jsx` + 子组件(`chat/`、`ocr/` 等)
- 新增 API 模块:`ai-edu-front/src/api/modules/tutoring.js`(REST + SSE)
- 修改路由:`ai-edu-front/src/routes.jsx`(student children 增加 `ai-qa` 路由)
- 修改常量:`pageMeta.js`(STUDENT_AI_QA active)、`constants/index.js`(已有 ROUTES.STUDENT_AI_QA,不变)
- 复用:`request.js`(axios,非流式)、`remark-math` + `rehype-katex`(公式渲染)、`EmptyState`/`Toast`、daisyUI + Tailwind
- 不引入新依赖;不修改 `AIChatPanel` / `llm.js`(通用助手与答疑是两个功能,各自独立)
- 依赖后端 `ai-tutoring` 已实现的接口(本仓库只消费,不改后端契约)
