# design-python-2026-08-12-tutoring-agent-protocol

> summary: 解决 tutoring agent 空流兜底的话术问题
> 权威度: 0.7 ｜ 来源: OpenSpec ｜ 锚点: 6. 空流兜底保留
> 模块: ai-tutoring ｜ 节: design-python-2026-08-12-tutoring-agent-protocol
> COS路径: ai-tutoring/rag-slices/OpenSpec/design-python-2026-08-12-tutoring-agent-protocol-6-空流兜底保留.md
> 类别：开发难点

---

### 6. 空流兜底保留

generate 零 token 时给固定引导话术(已实现于 `ai-tutoring`),避免空回复。
