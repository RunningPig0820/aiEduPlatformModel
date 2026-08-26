# SSE 事件流从头到尾的完整时序是什么？前端怎么消费这些事件？

> summary: 完整时序——agent(guardrail,Java) → meta → agent(generate,Python) → thinking* → token* → agent(memory,Java) → done。
> 权威度: 1.0 ｜ 来源: 引导问题 ｜ 锚点: SSE 事件流从头到尾的完整时序是什么？前端怎么消费这些事件？
> 模块: ai-tutoring ｜ 节: 业务流程图
> COS路径: ai-tutoring/rag-slices/引导问题/引导问题-52-业务流程图-SSE事件流从头到尾的完整时序是什么.md
> 类别：业务流程

## 回答

**核心结论**：完整时序——agent(guardrail,Java) → meta → agent(generate,Python) → thinking* → token* → agent(memory,Java) → done。

**分层展开**：
- **decide 阶段**：agent(perceive→analyze→plan→decide) 实时中继 + thinking 推理分片，前端"意图解析中"live 走查。
- **meta 先行**：已放行 type 先到（sessionId/status/type/roundCount/eval/masterySignals），前端据此渲染气泡类型再收正文。
- **generate 阶段**：thinking（推理流）与 token（正文流）并行，最后 agent(memory,Java)（落库收尾信号）+ done（status/summary/endReason）。
- **前端消费**：按 stage 去重（processing→done 就地更新）；meta 到达即持久化 localStorage；done 落终态判定 ARCHIVED/TERMINATED；SSE 看门狗防长时间无事件误判。
- **事件协议**：agent 事件标准格式 {level, stage, label, status, detail}，stage 闭集 8 阶段（perceive/analyze/plan/tool/decide/generate/memory/guardrail）。
- **追问点**："thinking 是模型真实推理吗？" → 是，直连方舟读原始 SSE 的 reasoning_content——不是模拟，是真实推理分片，也是"AI 版进度条"。
