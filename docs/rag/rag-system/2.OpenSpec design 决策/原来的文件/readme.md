# 原来的文件（spec 归档：高价值整理为 RAG 版 + 中/低价值原始证据）

> 用途：三端（Java / 前端 / Python）RAG 相关 OpenSpec 素材归档。**23 份高价值已整理为 RAG 版**（流水线A：`###` 分块 + 状态/检索摘要，权威 0.7，按 ### 切进切片池）；**3 份中价值**（api/known-issues）与 **15 份低价值**（交付编排组/proposal）保留原始证据。
> 归档时间：2026-08-28。命名：`{类型}-{端}-{change}-{spec}.md`。
> 价值分层：41 份 = **23 高（本目录根，RAG 版）** + **3 中（`中价值/`）** + **15 低（`低价值/`）**。

## 归档清单（41 份 = 23 高[RAG版] + 3 中 + 15 低）

### Java 后端（aiEduPlatform）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-java-rag-project-intro-assistant.md`（1，RAG版） | `openspec/changes/rag-project-intro-assistant` | 08-25 白盒链 D1~D12+契约+编排，24 块 |
| `spec-java-rag-project-intro-assistant-{gateway,pipeline,resilience,eval,guardrails}.md`（5，RAG版） | 同上 `specs/*/spec.md` | 白盒流水线 5 大块（角色门/意图SSE/召回重排/评测/护栏），7/6/8/7/9 块 |
| `design/proposal/api/spec-...-milestone-{01..07}.md`（10） | `openspec/changes/archive/2026-08-25-rag-assistant-incremental-delivery` | ⚠️ **低价值** → `低价值/`（交付编排已被主 design 吸收，需求为主 spec 复述） |

### 前端（aiEduPlatformFront）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-frontend-rag-assistant-frontend.md`（1，RAG版） | `openspec/changes/add-rag-assistant-frontend` | 前端白盒 UI 交互，16 块 |
| `spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（1，RAG版） | 同上 `specs/rag-assistant-ui/spec.md` | 引导 chips/白盒面板/召回可视化 UI，12 块 |

### Python AI 服务（aiEduPlatformModel）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-python-project-intro-rag.md`（1，RAG版） | `openspec/changes/project-intro-rag` | 08-21 设计（双池/页面锚定/两道门/token真算），16 块 |
| `spec-python-project-intro-rag-{rag-corpus,rag-permission,rag-retrieval,rag-generation,rag-resilience}.md`（5，RAG版） | 同上 `specs/*/spec.md` | 5 大块拆分，5/2/6/4/5 块 |
| `design-python-rag-eval-agent.md`（1，RAG版） | `openspec/changes/rag-eval-agent` | 评测 agent（hit@k + answer_quality），12 块 |
| `spec-python-rag-eval-agent-{eval-agent,eval-observability,kb-organization}.md`（3，RAG版） | 同上 | 判分/可观测/知识库状态机，5/3/3 块 |
| `design-python-rag-project-intro-assistant.md`（1，RAG版） | `openspec/changes/rag-project-intro-assistant-python` | 08-25 白盒透传（硬路由/Query改写/is_quoted），14 块 |
| `spec-python-rag-project-intro-assistant-{pipeline,resilience,eval,guardrails}.md`（4，RAG版） | 同上 | 白盒流水线 Python 侧，6/7/5/8 块 |

## 价值分层说明

- **23 高价值（RAG 版）**：流水线A 整理，`###` H3 分块 + `> 状态:` + `> 检索摘要:`，权威 0.7，`doc_type=design_spec`，按 `###` 切进切片池。**原始 spec 版可从 openspec 源仓库恢复**（`aiEduPlatform/`、`aiEduPlatformFront/`、`aiEduPlatformModel/` 各 `openspec/changes/`）。
- **`中价值/`（3 份）**：`api-*.md`（2）+ `known-issues-*.md`（1），接口契约 / 已知问题，供 方案-代码对账 与 坑档案 引用，不进语料。
- **`低价值/`（15 份）**：`rag-assistant-incremental-delivery` 交付编排组（10，已被主 design 吸收）+ proposal（5，同源精简版），详见 `低价值/readme.md`。

> 切片输入：`切片数据/OpenSpec` 切片器读取本目录根的 23 份 RAG 版（`原来的文件/*.md`，排除子目录）。
> 参照 question-analysis / knowledge-graph Phase：spec 先价值评估再处置 → 高价值流水线A 成文（进池 0.7）+ 流水线B 收敛 canonical（0.8）。
