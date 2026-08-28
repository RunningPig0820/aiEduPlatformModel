# 产品定位与核心价值

> summary: 产品定位与核心价值（design-java-rag-project-intro-assistant）：一鱼两吃——产品讲清项目、RAG 证明能力，学生向白盒 RAG 项目介绍助手，区别于 08-21 面试 demo
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/design-java-01-产品定位与核心价值.md
> 类别：项目介绍

---

### 业务背景与定位(Context)

> 检索摘要：白盒RAG项目介绍助手(Java侧)为什么做、定位是什么？学生页面提问走权限→意图→召回→RRF→生成全链路SSE透传，产品=讲清项目、RAG=证明能力，复用tutoring网关与Python已有RAG链路，区别08-21面试demo

面向学生的 **RAG 项目介绍助手**(`rag-project-intro-assistant`):学生可在项目页面内就本项目设计逻辑提问(项目介绍 / 操作流程 / 数据关联 / 难点),回答遵循 RAG 标准链路并把中间状态白盒透传前端。这不是纯 RAG——产品是"讲清项目",RAG 是证明能力的引擎。

**现状约束与可复用资产**:
- **Python 侧已有单模块 RAG 链路**:`ai-edu-ai-service/core/rag/query.py` 已实现 `classify(LLM→关键词兜底)` → `retrieve_vector(COS)` + `retrieve_bm25(本地jsonl)` → `orchestrate(RRF×authority×锚定)` → `generate(doubao)`,含 `references`(file/file_path/anchor/authority/summary)、usage 统计、降级链(向量挂→纯BM25;doubao挂→返回召回块;置信度低→拒答)。语料 `scripts/rag/data/rag_slices.jsonl`(234 块)为 **AI答疑模块唯一已切片入库数据**。
- **评估链已存在**:`run_eval.py`(CLI/API,`--compare` 版本对比) → `eval_agent.py`(`hit_at_k`/`judge_quality`/`calc_cost`/`aggregate`) → `eval_dataset.py`(格式校验,5 类型闭集,每模块 ≥5 条)。已有 baseline 报告:hit@3=0.80、质量分=4.2/5、耗时≈5.6s、成本≈¥0.016。
- **tutoring 两段式可复用**:Java 网关编排(安全预检→组装上下文→Python decide 非流式→护栏→generate 流式 SSE 透传)已验证;`SseMetaDTO`/`SseMasterySignalDTO` 事件 DTO、snake↔camel 契约纪律(`@JsonProperty`、`FAIL_ON_UNKNOWN_PROPERTIES=false`、degraded 走 200 不走 503)均为既有约定。
- **前端**:学生已有 AI答疑页(AiQa.jsx)与相关 hooks,RAG 助手前端另立变更,本设计只定后端契约。

**定位说明**:本变更与 Model 仓库 08-21 `project-intro-rag` 设计**方向不同**——后者是面试官 demo、覆盖 4 业务页、`role` 走 body;本变更是**学生**、仅讲 RAG 项目自身(AI答疑模块有语料)、角色走可信 session。**实现上泛化已有 `/api/tutoring/rag/query`,不照搬 08-21 的双池 QA 设计**(保留其"范围门=检索置信度"与"预写答案兜底"思想)。

> 证据：详见 `2.OpenSpec design 决策/原来的文件/design-java-rag-project-intro-assistant.md`（§业务背景与定位(Context)）
