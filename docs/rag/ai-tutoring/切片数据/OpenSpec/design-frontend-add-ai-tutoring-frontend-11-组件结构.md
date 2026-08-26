# design-frontend-add-ai-tutoring-frontend

> summary: 说明AI辅导前端的组件结构与各模块职责
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 11. 组件结构
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-frontend-add-ai-tutoring-frontend-11-组件结构.md
> 类别：架构设计

---

### 11. 组件结构

```
pages/student/AiQa.jsx              — 页面容器:useTutoringSession + 布局
components/student/ai-qa/
  CurrentQuestionCard.jsx           — 当前题目置顶卡片(纯展示、可折叠)
  ChatThread.jsx                    — 消息列表 + 流式光标 + 空状态
  MessageBubble.jsx                 — 用户/AI 气泡;AI 带 TypeBadge + markdown/katex + 重试
  TypeBadge.jsx                     — type → 文案/颜色映射
  KpChips.jsx                       — 知识点 chips(条件渲染)
  ChatInput.jsx                     — 📷 OCR、textarea、请求答案、发送、禁用态
  OcrConfirmModal.jsx               — OCR 识别确认/修改弹窗
  SessionSummary.jsx                — 收尾总结卡片 + 再来一题
  HistorySidebar.jsx                — 历史会话常驻左栏(桌面,DeepSeek 式)/移动端汉堡拉出 overlay(方案 A 演进,替代原抽屉)
hooks/useTutoringSession.js         — 会话状态机 / SSE 消费 / localStorage 持久化 / 对账
api/modules/tutoring.js             — API + SSE 客户端(决策 2)
```

路由/常量:
- `routes.jsx`:student children 增加 `{ path: 'ai-qa', element: <AiQa /> }`
- `pageMeta.js`:STUDENT_AI_QA `status: 'active'`,features 去掉"语音问答"
- `routes.jsx` studentMenu:AI答疑 status → `'active'`
