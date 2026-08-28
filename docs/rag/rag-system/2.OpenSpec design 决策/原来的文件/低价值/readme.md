# 低价值 spec 归档（15 份，保留备查，不进 RAG、不参与对账主流程）

> 用途：**低价值但保留证据**——被更高价值文档覆盖/吸收，或仅过程性编排。留作溯源，不参与 RAG 语料与对账主流程。
> 价值判定时间：2026-08-28。判定标准：①内容被另一份已保留文档完全覆盖；②仅交付过程编排、无系统设计增量。

## ① rag-assistant-incremental-delivery 归档组（10 份）——交付编排，已被主 design 吸收

`design-java-rag-project-intro-assistant.md`（高价值，根目录）已含「交付编排（并入自 rag-assistant-incremental-delivery，2026-08-25 归档）」节（M1-M8 里程碑/桩替策略/完成标准/对接节奏）。本组只剩编排层 + 对主 spec 的需求复述，无独立系统知识增量。

| 文件 | 低价值原因 |
|---|---|
| `design-java-rag-assistant-incremental-delivery.md` | 纯交付编排（自身声明"不做新的系统行为，只编排何时交付什么"） |
| `proposal-java-rag-assistant-incremental-delivery.md` | 同源精简版 |
| `api-java-rag-assistant-incremental-delivery.md` | 接口契约复述（与主 api 同源） |
| `spec-java-rag-assistant-incremental-delivery-milestone-01~07.md`（7） | 需求为主 spec（gateway/pipeline/resilience/eval/guardrails）复述 + 里程碑编排 |

## ② proposal（5 份）——同源精简版

Why/What 被对应 `design-*.md`（Context + Decisions）完全覆盖，无增量。沿用 question-analysis / knowledge-graph 惯例：proposal 一律归档不进池。

| 文件 | 对应高价值 design |
|---|---|
| `proposal-java-rag-project-intro-assistant.md` | `design-java-rag-project-intro-assistant.md` |
| `proposal-frontend-rag-assistant-frontend.md` | `design-frontend-rag-assistant-frontend.md` |
| `proposal-python-project-intro-rag.md` | `design-python-project-intro-rag.md` |
| `proposal-python-rag-eval-agent.md` | `design-python-rag-eval-agent.md` |
| `proposal-python-rag-project-intro-assistant.md` | `design-python-rag-project-intro-assistant.md` |

> 恢复/删除：若未来需要 proposal 的 Why 叙述原文，openspec changes 源目录仍在（`aiEduPlatform/`、`aiEduPlatformFront/`、`aiEduPlatformModel/` 各 `openspec/changes/`）。
