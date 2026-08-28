# 原来的文件（RAG 版 spec 归档）

> 用途：三端（Java / 前端 / Python）RAG 相关 OpenSpec 素材，**整理为 16 份高价值 RAG 版**（流水线A：`###` 分块 + 状态/检索摘要，权威 0.7，按 ### 切进切片池）。
> 归档时间：2026-08-28。命名：`{类型}-{端}-{change}-{spec}.md`。
> 演进：41 份原始 spec 归档 → 价值分层（23 高/3 中/15 低）→ 高价值整理 RAG 版 23 → 去重合并（7 次高并入 design）→ **最终保留 16 份高价值 RAG 版**；中/低/次高原始证据已删（git 历史可恢复）。

## 归档清单（16 份高价值 RAG 版）

### Java 后端（aiEduPlatform）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-java-rag-project-intro-assistant.md` | `openspec/changes/rag-project-intro-assistant` | 08-25 白盒链 D1~D12+契约 D-A~E+编排 M1-M8，24 块 + 4 补充节（并入 Java pipeline/resilience/eval/guardrails 独有内容） |
| `spec-java-rag-project-intro-assistant-gateway.md` | 同上 `specs/rag-assistant-gateway/spec.md` | 角色门/SSE 中继/trace_id/source 代理（Java 独有），7 块 |

### 前端（aiEduPlatformFront）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-frontend-rag-assistant-frontend.md` | `openspec/changes/add-rag-assistant-frontend` | 前端白盒 UI 交互，16 块 |
| `spec-frontend-rag-assistant-frontend-rag-assistant-ui.md` | 同上 `specs/rag-assistant-ui/spec.md` | 引导 chips/白盒面板/召回可视化 UI，12 块 |

### Python AI 服务（aiEduPlatformModel）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-python-project-intro-rag.md` | `openspec/changes/project-intro-rag` | 08-21 设计（双池/页面锚定/两道门/token真算），16 块 + 3 补充节（并入 08-21 retrieval/generation/resilience 独有内容） |
| `spec-python-project-intro-rag-{rag-corpus,rag-permission}.md` | 同上 `specs/*/spec.md` | 语料构建/权限前置（独有），5/2 块 |
| `design-python-rag-eval-agent.md` | `openspec/changes/rag-eval-agent` | 评测 agent（hit@k + answer_quality），12 块 |
| `spec-python-rag-eval-agent-{eval-agent,eval-observability,kb-organization}.md` | 同上 | 判分/可观测/知识库状态机，5/3/3 块 |
| `design-python-rag-project-intro-assistant.md` | `openspec/changes/rag-project-intro-assistant-python` | 08-25 白盒透传（硬路由/Query改写/is_quoted），14 块 |
| `spec-python-rag-project-intro-assistant-{pipeline,resilience,eval,guardrails}.md` | 同上 | 白盒流水线 Python 侧（引擎实现真相），6/7/5/8 块 |

## 说明

- 16 份 RAG 版：流水线A 整理，`###` H3 分块 + `> 状态:` + `> 检索摘要:`，权威 0.7，`doc_type=design_spec`，按 `###` 切进切片池。
- 原始 spec 版可从 openspec 源仓库恢复（`aiEduPlatform/`、`aiEduPlatformFront/`、`aiEduPlatformModel/` 各 `openspec/changes/`）。
- 切片输入：`切片数据/OpenSpec` 切片器读取本目录根 16 份 RAG 版（`原来的文件/*.md`，排除 readme）。
