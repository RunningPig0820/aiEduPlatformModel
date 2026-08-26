# SSE流式输出中途断连，学生重新进入会话，系统如何恢复现场，哪些信息需要重推前端？

> summary: SSE流式输出中途断连，学生重新进入会话，系统如何恢复现场，哪些信息需要重推前端？
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: SSE流式输出中途断连，学生重新进入会话，系统如何恢复现场，哪些信息需要重推前端？
> 模块: ai-tutoring ｜ 节: 线上稳定性
> COS路径: rag-slices/ai-tutoring/引导问题/引导问题-75-线上稳定性-SSE流式输出中途断连学生重新进入会.md
> 类别：开发难点

## 回答

**核心结论**：前端 meta 早持久化 + 会话 ACTIVE 保持 + 后端代理读历史，断连后恢复现场、续走会话，不重复建会话。

**分层展开**：
- **持久化**：meta 到达即写 localStorage（sessionId 幂等，F2 修复——原来只在 done 落库，generate 中断就丢 sessionId）→ 刷新后挂载恢复续走 sendMessage。
- **断连处理**：Python stream_generate 每轮 request.is_disconnected() 检测 → 中止在途生成；Java 已执行的落库副作用保留，未 generate 完的本轮可重试。
- **恢复重推**：重新进入会话由 Java 从 Redis 组装历史（question/answer 逐轮）+ 掌握度快照 + 护栏计数；transcript 由后端代理读（前端零 COS 直连，J10 修复）。
- **前端兜底**：SSE 看门狗长时间无事件判流断 → 回退可重试态；50002（会话已清）清理 localStorage 陈旧条目。
- **追问点**："哪些信息需要重推？" → 历史对话、会话状态（ACTIVE/终态）、护栏计数（轮次/答案次数）、掌握度快照——保证续走时上下文一致。
