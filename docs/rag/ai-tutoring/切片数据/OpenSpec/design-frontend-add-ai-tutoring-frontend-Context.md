# design-frontend-add-ai-tutoring-frontend

> summary: 讲前端需消费后端AI答疑协议，补全学生端答疑页面
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Context
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> COS路径: rag-slices/ai-tutoring/OpenSpec/design-frontend-add-ai-tutoring-frontend-Context.md
> 类别：项目介绍

---

## Context

学生端 AI 答疑由后端 `ai-tutoring` 方案(兄弟仓库)提供完整能力:Java 网关编排(安全 → decide → 护栏 → generate),SSE **类型先行流式**协议(`meta` → `token` → `done`),拍题 OCR 前置,掌握度落库。前端 `ai-edu-front`(React + Vite + daisyUI)已有 `/student/ai-qa` 路由常量与侧边栏菜单(status=pending),但**没有页面**,点击 404。

本设计解决"前端如何消费这套协议并承载苏格拉底式引导的交互"。前端只消费后端已定契约,**不改后端**;两个已识别的契约缺口(活跃会话查询接口、OCR 开关配置)经讨论**不做后端新增**,分别用本地持久化与常驻拍照按钮规避。

约束:
- 学生端角色色 = success(绿);整页风格走现代网页 AI 智能体交互(ChatGPT/DeepSeek web 风)
- 现有 `AIChatPanel`(通用管理助手抽屉)与 `llm.js` SSE 客户端**不改不动**,答疑是独立功能
- 复用 `request.js`(axios 非流式)、`remark-math` + `rehype-katex`(公式)、daisyUI + Tailwind、`EmptyState`/`Toast`
- 不引入新 npm 依赖
