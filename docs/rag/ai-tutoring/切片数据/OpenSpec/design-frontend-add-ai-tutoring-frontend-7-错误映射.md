# design-frontend-add-ai-tutoring-frontend

> summary: 讲AI答疑各错误码对应的前端处理方式
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 7. 错误映射
> 模块: ai-tutoring ｜ 节: design-frontend-add-ai-tutoring-frontend

---

### 7. 错误映射

| 错误 | 前端表现 |
|---|---|
| 50002 会话不存在 | 本地快照降级为历史回看,引导"发起新会话" |
| 50003 已结束/已归档 | 展示该会话 ended 视图,不可再发消息 |
| 50004 创建过于频繁 | toast"请先完成当前答疑" |
| 50005 agent 失败 | toast"网络波动,请重试";保留该 user 气泡并附"重试"(重发同内容);会话保持 ACTIVE |
| 50006 OCR 无效 | toast"请重新上传清晰照片" |
| SSE 中途断开 | 流式气泡显示"回复中断"+"重试"按钮(重发最近一条 user 消息) |
