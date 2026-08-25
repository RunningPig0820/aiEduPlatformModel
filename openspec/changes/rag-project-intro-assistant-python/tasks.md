# Tasks: RAG 项目介绍助手 - Python 白盒链路

> 对齐后端：`aiEduPlatform/openspec/changes/rag-project-intro-assistant`（design D1~D12 + specs×4 + api.md）
> 沟通定稿：C1 语料范围(仅AI答疑, 其他模块低置信拒答正确) / C2 anchor两层(模块选池+节加权) / C3 cache_hit实测 / C4 clarify候选(LLM+会话锚点) / C5 suggestions必含RAG
> 联调审查定稿（2026-08-25）：① ask 请求带 history/trace_id(Java 传) ② permission 仅 Java(Python 生产不产) ③ turns 存 Java Redis ④ close 归 Java(Python 不建端点) ⑤ intent 事件含 candidates ⑥ switch 补 spec+任务 ⑦ history 显式截断 N=3 ⑧ tasks 标 Java 归属
> 标注：【复用】改现有 /【新增】新建 /【扩展】现有加能力
> ↔ **Java 侧里程碑对照**：A 组↔Java M2(引擎) / B 组↔M3(网关) / C 组↔M4(韧性) / D 组↔M5(评估)，联调时对表

## A. 白盒链路引擎（core/rag/assistant.py 新增编排 + 泛化 query.py）

### A1. intent 结构化输出
- [x] 【扩展】`classify` 升级为 `intent(question, history)`：LLM 输出 `{anchor, category, switch_detected, ambiguous, candidates}`（复用 `_llm_category` 的 doubao 连接 + 0 温度关思考）
- [x] 【复用】失败/非闭集 → `_fallback_anchor` + `ANCHOR_RULES` 兜底，degraded 标记（现有逻辑保留）
- [x] 【新增】schema 校验：anchor 必填模块 id、candidates 闭集去重、switch/ambiguous 布尔
- [x] 【新增】**history 截断**：`history[-N:]`（N=3 默认，含 clarify 轮），Java 传入 Python 只消费（联调 ⑦）

### A2. rewrite 改写
- [x] 【新增】`rewrite_query(question, anchor, history)`：口语→检索式改写（LLM 短调用），失败返回原问题（history 截断同 A1）

### A2b. switch 上下文切换（联调 ⑥ 补 spec+任务）
- [x] 【新增】**switch 重置上下文**：intent 检测 switch_detected → 重置锚点/召回/轮次计数 → 走新锚点 rewrite→recall→generate
- [x] 【新增】switch 事件 `{from_anchor, to_anchor}` + 上下文重置（对齐 Java D3）
- [x] 【新增】switch 的 spec 需求：补进 guardrails spec（见 specs/guardrails 增加 Requirement）

### A3. recall 双路 + anchor 选池
- [x] 【复用】`retrieve_vector` / `retrieve_bm25`（现有）
- [x] 【扩展】orchestrate 入参加 `corpus`：anchor 明确 → 先按 module 过滤语料池，再 RRF×权威×节锚定加权（C2，锚定公式原样）
- [x] 【新增】单路 2s 超时包裹（asyncio.wait_for + run_in_threadpool），超时降级空路 + degraded 标记

### A4. rerank 精排 Top-K
- [x] 【扩展】orchestrate 只回传精排 Top-K（默认 3），不吐全量召回
- [x] 【新增】块结构 `{blockId, title, summary, filePath, score}`（映射现有 block → 前端契约）

### A5. generate 流式化
- [x] 【新增】`stream_generate(hits, query, request)`：复用 `ark_stream.stream_chat` 流式 yield token 增量
- [x] 【新增】8s 超时 → 写死降级话术 + 召回清单
- [x] 【新增】`request.is_disconnected()` 检测 → 中止上游 doubao 流
- [x] 【新增】`include_usage` 取流结束 usage → tokens_usage

### A6. is_quoted 确定性引用
- [x] 【新增】`lcs_quote_match(answer, block_texts) -> quoted_keys`：连续 8 中/12 英字符 LCS 硬匹配，纯函数
- [x] 【新增】done 后补发 quotedKeys（chunk 粒度不实时匹配）

### A7. clarify 澄清轮
- [x] 【新增】ambiguous & candidates≥2 → clarify 事件（固定话术 + candidates + default），0 token 不计轮次
- [x] 【新增】候选判定：LLM candidates 主源 + 会话历史锚点兜底 + <2 不触发（C4）
- [x] 【新增】最多一轮，仍模糊直接默认 current_project

### A8. suggestions 引导
- [x] 【新增】`gen_suggestions(answer, anchor)`：LLM 生成 1~3 条，prompt 约束必含 ≥1 条 RAG 方向（C5）
- [x] 【新增】LLM 失败 → 静态池兜底（预写含 RAG 方向文案）

### A9. 范围门低置信过滤
- [x] 【新增】rerank 空 → boundary；非空但双路召回置信度都低于阈值（vec<0.75 且 bm<0.5）→ boundary(low_confidence) 固定话术，不调 generate（**阈值用召回置信度 0-1，非 RRF 相对分**——真链路冒烟发现初版量级错位全误拒）
- [x] 【新增】唯一拒答路径：无禁区硬拒答，全由低置信触发（C1）

## B. 白盒 API（api/rag_assistant.py 新增）

> **boundary 短路纪律（冒烟定稿 2026-08-25）**：boundary 触发 → 发 boundary 事件后**立即 done，不调 generate**（0 token）。真链路冒烟确认：rerank 空时 doubao 会自生成"未覆盖"话术（32 token）——编排器必须短路防无谓生成成本。

- [ ] 【新增】`POST /api/rag/assistant/ask` SSE 流式：事件时序 intent→(clarify|switch)→rewrite→rerank→(boundary|token)→done（冻结，不重排；**permission 由 Java 产，Python 生产端点不产**）
- [ ] 【新增】`POST /api/rag/assistant/ask` 非流式：done 结构 + stages 摘要（intent/rewrite/rerank）
- [ ] 【新增】请求消费 `history` + `trace_id`（Java 传入，Python 只用；done 回显 trace_id）
- [ ] 【新增】`GET /api/rag/assistant/eval/report`：baseline 报告白盒
- [ ] 【新增】`GET /api/rag/assistant/guide`：开始引导（静态池 RAG 定向）
- [ ] 【复用】鉴权 `verify_internal_token`（同现有 API）
- [ ] 【新增】`is_disconnected()` 中止在途流（close 由 Java 关中继触发，Python 不建 close 端点）

## C. 健壮性（resilience）

- [ ] 【新增】分层超时参数化：`RAG_RECALL_TIMEOUT=2` / `RAG_GEN_TIMEOUT=8`（settings）
- [ ] 【新增】写死降级话术常量（low_confidence / gen_timeout / closed）
- [ ] 【新增】tokens_usage 组装（prompt/completion/cache_hit/total；cache_hit 取不到 → tokenizer 估算标注，C3）
- [ ] 【新增】断连取消测试：SSE 生成中 is_disconnected → 中止

## D. 评估扩展（eval）

- [ ] 【扩展】`eval_dataset.VALID_TYPES` 加 `边界拒答`；断言 = 触发固定话术且 0 token
- [ ] 【新增】`precision_at_k` 纯函数（top-k 相关块占比）
- [ ] 【新增】is_quoted 校验：quotedKeys ⊆ 召回块，入评估
- [ ] 【新增】baseline 报告经 eval/report 白盒展示（hit@k/质量分/cost/latency）

## E. 测试

- [ ] 【新增】intent 测试（正常/失败兜底/非闭集）
- [ ] 【新增】rewrite 测试（口语改写/失败回退）
- [ ] 【新增】anchor 选池测试（orchestrate corpus 参数、锚定公式不变）
- [ ] 【新增】双路超时降级测试
- [ ] 【新增】SSE 事件时序测试（mock 各阶段，断言事件顺序）
- [ ] 【新增】is_quoted 纯函数测试（命中/改写未命中/8字窗口）
- [ ] 【新增】clarify 测试（多候选/澄清一次仍模糊/单候选不触发）
- [ ] 【新增】boundary 低置信测试（无语料模块拒答）
- [ ] 【新增】switch 测试（检测/重置上下文/新锚点链路）
- [ ] 【新增】history 截断测试（N=3 只取最近 3 轮）
- [ ] 【新增】断连取消测试
- [ ] 【新增】precision_at_k / 边界拒答评测测试
- [ ] 【回归】`/api/tutoring/rag/query` 现有测试全过（corpus 参数向后兼容）

## F. 交付

- [ ] 【交付】Python 侧自测全过（pytest）
- [ ] 【交付】对照后端 api.md 逐事件核对契约
- [ ] 【交付】写 `对接说明.md`（给前端/后端：端点/事件时序/引用面板/停止方式/鉴权）
