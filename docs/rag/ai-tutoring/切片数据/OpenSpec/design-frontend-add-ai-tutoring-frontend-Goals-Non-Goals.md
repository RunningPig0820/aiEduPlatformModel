# design-frontend-add-ai-tutoring-frontend

> summary: 明确AI答疑前端页面的目标与非目标范围
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: Goals / Non-Goals
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend

---

## Goals / Non-Goals

**Goals:**
- 整页答疑页面,AI 智能体交互风格,支持数学公式渲染与流式输出
- 消费类型先行 SSE:按 `meta.type` 渲染类型徽标,`denied` 场景按降级 type 渲染
- 拍题 OCR 前置:上传 → 识别文本确认/修改 → 作为首条消息发起会话
- 护栏可见性:轮次进度(≤20)、请求答案(第 1 次思路 / 第 2 次答案,第 2 次弹确认)、换题分隔提示、收尾总结卡片
- 断点恢复:localStorage 本地记录(DeepSeek 式)+ 服务端对账,不依赖后端新接口
- 知识点 chips 条件渲染(有 `masterySignals` 才显示),无前端知识点模块依赖

**Non-Goals:**
- 不实现后端 Python decide/generate/OCR(另仓排期)
- 不做语音问答(pageMeta 曾列,不在后端答疑范围)
- 不做图谱叠加页面本身(掌握度接口留给未来学生端知识图谱页消费)
- 不新增"换一题"按钮(换题=贴新题,语义判断在后端 decide)
- 不做多会话完整侧边栏/历史服务端列表(方案 A:仅本地最近 N 条)
