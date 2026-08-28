# 原来的文件（原始 spec 归档，不进 RAG）

> 用途：**证据源/人肉溯源底稿**。三端（Java / 前端 / Python）的 RAG 相关 OpenSpec 原始 design/proposal/spec/api 归档于此，`2.OpenSpec design 决策/` 根目录只保留进池的 RAG 版 `design-*.md`（设计成文，权威 0.7 按 ### 切）。
> 归档时间：2026-08-28。命名：`{类型}-{端}-{change}-{spec}.md`。
> 价值分层（2026-08-28）：41 份 = **23 份高价值**（本目录根：5 design + 18 spec）+ **3 份中价值**（`中价值/`：api×2 + known-issues，供对账/坑档案引用）+ **15 份低价值**（`低价值/`：交付编排组 + proposal，详见各子目录 readme）。

## 归档清单（41 份 = 23 高 + 3 中 + 15 低）

### Java 后端（aiEduPlatform）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-java-rag-project-intro-assistant.md`（1） | `openspec/changes/rag-project-intro-assistant` | 高价值 → 双轨（spec 信息补充 canonical + 成文进池） |
| `spec-java-rag-project-intro-assistant-{gateway,pipeline,resilience,eval,guardrails}.md`（5） | 同上 `specs/*/spec.md` | 白盒流水线 5 大块（角色门/意图SSE/召回重排/评测/护栏） |
| `design/proposal/api/spec-...-milestone-{01..07}.md`（10） | `openspec/changes/archive/2026-08-25-rag-assistant-incremental-delivery` | ⚠️ **低价值** → `低价值/`（交付编排已被主 design 吸收，需求为主 spec 复述） |

### 前端（aiEduPlatformFront）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-frontend-rag-assistant-frontend.md`（1） | `openspec/changes/add-rag-assistant-frontend` | 有产品/交互语义，保留 |
| `spec-frontend-rag-assistant-frontend-rag-assistant-ui.md`（1） | 同上 `specs/rag-assistant-ui/spec.md` | 引导 chips/白盒面板/召回可视化 UI |

### Python AI 服务（aiEduPlatformModel）

| 文件 | 来源 | 处置 |
|---|---|---|
| `design-python-project-intro-rag.md`（1） | `openspec/changes/project-intro-rag` | 08-21 设计（双池/页面锚定/两道门/token真算） |
| `spec-python-project-intro-rag-{rag-corpus,rag-permission,rag-retrieval,rag-generation,rag-resilience}.md`（5） | 同上 `specs/*/spec.md` | 5 大块拆分 |
| `design-python-rag-eval-agent.md`（1） | `openspec/changes/rag-eval-agent` | 评测 agent（hit@k + answer_quality） |
| `spec-python-rag-eval-agent-{eval-agent,eval-observability,kb-organization}.md`（3） | 同上 | 判分/可观测/知识库状态机 |
| `design-python-rag-project-intro-assistant.md`（1） | `openspec/changes/rag-project-intro-assistant-python` | 08-25 白盒透传（硬路由/Query改写/is_quoted） |
| `spec-python-rag-project-intro-assistant-{pipeline,resilience,eval,guardrails}.md`（4） | 同上 | 白盒流水线 Python 侧 |

## 与根目录 RAG 版 design 的关系

- 根目录 `design-python-project-intro-rag.md` / `design-python-rag-eval-agent.md` = 进池的**设计成文**（权威 0.7，按 ### 切进切片池），与归档 `design-*.md` **内容一致**（归档保留证据源 + 供对账引用）。
- 归档 `proposal-*.md`（6 份）= 同源精简版，Why 被 design Context 覆盖 → **低价值**，移入 `低价值/`。
- `中价值/`（3 份）= `api-*.md`（2）+ `known-issues-*.md`（1），接口契约 / 已知问题，供 方案-代码对账 与 坑档案 引用，详见 `中价值/readme.md`。
- `低价值/`（15 份）= `rag-assistant-incremental-delivery` 归档组（10 份，交付编排已被主 design 吸收）+ proposal（5 份），详见 `低价值/readme.md`。

> 参照 question-analysis / knowledge-graph Phase：spec 先价值评估再处置 → 归档 → 双轨（信息补充 canonical + 自身成文进池）。
