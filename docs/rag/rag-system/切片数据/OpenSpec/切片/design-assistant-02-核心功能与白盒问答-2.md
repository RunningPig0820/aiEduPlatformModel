# 核心功能与白盒问答（suggestions / 事件时序 / 非流式 / 迁移落地）

> summary: 核心功能与白盒问答 — suggestions 追问建议 + SSE 事件时序冻结 + 非流式 ask + 引擎迁移落地步骤
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-assistant-02-核心功能与白盒问答-2.md
> 类别：操作流程


### 沟通结论锁定（C5 suggestions）

> 检索摘要：08-25 锁定 suggestions 必含 RAG 方向——面试展示，RAG 始终带上非并列模块？

- **C5 suggestions**：必含 ≥1 条 RAG 方向（面试展示，RAG 始终带上非并列模块）。

### D-E. suggestions（D11）

> 检索摘要：suggestions 追问建议怎么生成——LLM 出 1~3 条、必含 RAG 方向、失败静态池兜底？

- done 后调一次 doubao（复用生成连接，0.2 温度）→ 1~3 条，prompt 约束"必含 ≥1 条 RAG 方向"（与 C5 一致）。
- LLM 失败 → 静态池兜底（预写 2~3 条固定文案，含 RAG 方向）。

### D-F. 事件时序冻结——定死 2026-08-25

> 检索摘要：SSE 事件时序冻结成什么样——为什么生产端点 Python 不产 permission 事件？

- 对齐后端：`permission → intent → (clarify|switch) → rewrite → rerank → (boundary|token) → done`，不得重排/丢失。
- **permission 归属定死**：production API Python **不产 permission**（角色门在 Java，Python 无角色信息）。Python 自测时在测试里模拟完整时序，生产端点从 intent 开始。

### D-G. 非流式 ask

> 检索摘要：非流式 ask 怎么返回——同一链路产出 done 结构加 stages 阶段摘要？

- `stream=false`：内部走同一链路，产出 `done` 结构 + `stages` 摘要（intent/rewrite/rerank），一次性 JSON。

### Migration Plan

> 检索摘要：Python 白盒引擎落地步骤——query 泛化、assistant router、评估扩展、交付联调？

1. `core/rag/query.py` 泛化：classify→intent 扩展、orchestrate 加 corpus、generate 流式化（独立函数，不动现有）。
2. 新增 `api/rag_assistant.py`：assistant router（ask/close/turns/eval/report），复用鉴权。
3. 新增 `core/rag/assistant.py`：白盒编排（intent/rewrite/recall/rerank/generate/is_quoted/clarify/suggestions）。
4. 评估扩展：eval_dataset 边界拒答类型 + precision_at_k + is_quoted。
5. 测试：pipeline 各阶段、SSE 事件时序、降级/超时/断连、评估新增。
6. 交付契约给前端/后端联调。
