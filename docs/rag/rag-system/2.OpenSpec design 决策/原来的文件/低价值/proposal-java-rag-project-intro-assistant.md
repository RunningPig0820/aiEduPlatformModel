## Why

学生需要一个能**证明 RAG 能力**、又能**讲清本项目（AI答疑/RAG 项目）设计逻辑**的白盒问答助手：不是纯 RAG，产品 = 面向学生的项目介绍问答，RAG = 证明能力的引擎。要求把 RAG 标准链路（权限控制 → 意图识别 → Query 改写 → 多路召回 → 重排 → 生成）的关键中间状态**实时透传前端**，让学生（和验收方）看到每个环节在发生什么，回答带可点击的召回原文。现有 Python 服务已实现单模块（AI答疑）RAG 链路 `/api/tutoring/rag/query`（RRF 融合 + 双路召回 + LLM 意图分类 + 引用 + cost），但**非流式、无角色门、无白盒事件、无切换/澄清、无 is_quoted、无分层超时**，且 Java 侧完全没有对应网关。

## What Changes

- **Java 网关（本仓库）**：新增 `RagAssistantController`，从可信 session 取角色（STUDENT 才放行，非学生/缺失 → 固定 403，**不进入 RAG 流程、不消耗 token**）；SSE 中继 Python 白盒事件（permission → intent → rewrite → rerank → token → done），复用 tutoring 的 SSE 中继模式（`SseMetaDTO`/事件时序稳定契约）。
- **Python 引擎（aiEduPlatformModel 仓库，本变更定义契约）**：泛化已有 `core/rag/query.py` 为多模块白盒链路：
  - **intent（LLM 结构化输出）**：输出 `{anchor, category, switch_detected, ambiguous}`；失败回退关键词锚定（复用 `_fallback_anchor`）；四模块（AI答疑/知识图谱/题型分析/RAG）全放行，无禁区硬拒答。
  - **rewrite**：改写后 query 透传前端。
  - **recall**：双路召回（向量 + BM25），单路 2s 硬超时降级为纯另一路。
  - **rerank**：RRF 融合 → Top-K（建议 K=3），仅回传精排后块（标题/摘要/file_path），不吐全量召回。
  - **generate**：doubao 流式，8s 硬超时 → 固定降级话术返回召回清单；`is_disconnected()` 感知前端断开 → 中止流。
  - **is_quoted**：生成完成后对精排块做 LCS 硬匹配（任意连续 8 中文字符 / 12 英文字符命中即 quoted），非 LLM 自述，`done` 后补发 `quoted_keys`。
  - **clarify**：歧义（`ambiguous=true` 且存在多候选功能）→ 固定澄清话术 + 默认当前功能，**不计入答案轮次、0 token**；最多一轮，再模糊直接默认当前功能。
  - **tokens_usage**：`{prompt_tokens, completion_tokens, cache_hit_tokens, total_tokens}` + `trace_id`（取不到 cache_hit → tokenizer 估算标注）。
  - **问题提示**：**开始引导**（会话入口，静态池定向 RAG，0 token，非 SSE 接口 `GET /guide`）+ **结束建议**（每轮完成后，运行时 LLM 生成 1~3 条，向 ①项目介绍 ②操作流程 ③数据关联 ④难点，**必含 ≥1 条 RAG 方向**——RAG 是始终在底层运行的引擎、非展示页模块，每次问题提示都带上 RAG）。
  - **评估**：复用 `run_eval.py`/`eval_agent.py` 链路，新增 `边界拒答` 评估类型 + `precision_at_k` + is_quoted 纯函数校验；baseline 报告（hit@3/质量分/成本/耗时）供白盒展示"怎么证明有效"。
- **知识库**：多模块语料按模块目录组织，`rag_slices.jsonl` 为 AI答疑模块现状；四模块全放行，其它模块暂无切片时正常召回但命中为空/低置信 → 范围门低置信度过滤（固定话术，reason=low_confidence）（**最兼容：按语料有无数据驱动，未来入库即自动可答**）。
- **硬路由**：问题涉及"系统架构/代码实现/部署流程/评测方案/接口设计" → 强制路由 RAG 项目知识库；无禁区模块硬拒答，拒答均由范围门低置信度触发。

## Capabilities

### New Capabilities
- `rag-assistant-gateway`: Java 侧 RAG 项目介绍助手网关——角色门（仅 STUDENT）、SSE 白盒事件中继、trace_id 透传、会话续接（无状态单轮）、显式关闭对话
- `rag-assistant-pipeline`: Python 侧白盒 RAG 链路（intent/rewrite/recall/rerank/generate）与事件契约
- `rag-assistant-guardrails`: 模块全放行（四模块无禁区）+ 范围门低置信度过滤（唯一拒答路径）、clarify 澄清轮、is_quoted 硬匹配、模块可用性数据驱动、问题提示（开始引导定向 RAG + 结束建议必含 RAG）
- `rag-assistant-resilience`: 分层超时（召回 2s / 生成 8s）、断连取消、降级话术、上下文窗口截断（最近 3 轮）、tokens_usage + trace_id、会话累计 token（关闭对话结算）
- `rag-assistant-eval`: 评估集扩面（边界拒答类）、precision_at_k、is_quoted 校验、baseline 报告复用

### Modified Capabilities
<!-- 无既有 spec 需求变化：ai-tutoring / tutoring-agent-workflow-backend 需求不变，RAG 助手为独立新模块（复用 SSE 中继模式，不改其契约） -->

## Impact

- **本仓库（ai-edu-backend）**：
  - 新增 `ai-edu-interface` 控制器 `RagAssistantController`（`POST /api/rag/assistant/ask` 等，SSE 流式 + 非流式），学习域下答疑子模块新增 RAG 助手应用服务
  - 新增 `ai-edu-domain` 端口与 DTO（Python 契约 snake→camel 映射，沿用 `FAIL_ON_UNKNOWN_PROPERTIES=false`）
  - 复用 `LlmGateway`/`TutoringLlmClient` 的 internalToken 调用模式
- **aiEduPlatformModel 仓库**（本变更定义契约，实现在其 `rag-project-intro-assistant-python` 对应变更）：
  - 泛化 `core/rag/query.py`：intent 结构化输出、rewrite、clarify、is_quoted、白盒 SSE 事件、分层超时、断连取消、问题提示（开始引导 `GET /guide` + 结束建议必含 RAG）
  - `config/settings.py`：多模块语料路由、模型/温度、超时参数
  - 新增 `/api/rag/assistant/*` 内部端点（`x-internal-token`）
  - `scripts/rag/`：评估集扩面 + `precision_at_k` + 边界拒答类型
- **依赖**：无新增（doubao / dashscope / COS / jieba / run_eval 均已就绪）
- **前端（aiEduPlatformFront）**：需新增学生侧 RAG 助手页（开始引导 chips + 结束引导 chips + 白盒阶段展示 + 引用面板 + 成本面板），本变更仅定义后端契约，前端另立变更
