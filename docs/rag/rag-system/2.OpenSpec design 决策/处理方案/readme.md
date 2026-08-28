# 2.OpenSpec design 决策 处理方案

> 状态：2026-08-28 归档完成——2 份 proposal（低价值同源精简版）已 `mv` 入 `原来的文件/`；2 份 design 留根目录作 RAG 版成文（按 `###` 切进池 0.7）。设计决策收敛进 `1.语雀/` canonical（权威 0.8）。
> 权威度：design 素材固定 **0.7**（0.8 只给 canonical 真相源与代码分析）。OpenSpec 是本模块**意图层/方案口径**，不是检索主体。

## 一、本模块 OpenSpec 原料盘点

| 文件 | 性质 | 处置 |
|---|---|---|
| `design-python-project-intro-rag.md` | 高价值 design（RAG 版成文：双池/页面锚定/两道门/token 真算/降级矩阵） | ✅ 留根目录，按 `###` 切进池 0.7 |
| `design-python-rag-eval-agent.md` | 高价值 design（RAG 版成文：评测 agent hit@k + answer_quality） | ✅ 留根目录，按 `###` 切进池 0.7 |
| `proposal-python-project-intro-rag.md` | 低价值同源精简版（proposal，与 design 同源、无新增事实） | ⚠️ 已 `mv` 入 `原来的文件/` 归档，不进池 |
| `proposal-python-rag-eval-agent.md` | 低价值同源精简版（proposal） | ⚠️ 已 `mv` 入 `原来的文件/` 归档，不进池 |

> 判断标准：proposal 是 change 提案的轻量描述，与 design 同源且更精简、事实密度低；design 是成文版本（含完整 Decisions/Risks/OpenQuestions），才是切片进池的原料。**低价值同源文档用 `mv`（不是复制）归档**，保持根目录干净、双轨各就各位。

## 二、处理步骤（本模块流程）

1. **判断 spec 业务含义**：逐份 OpenSpec 文件判断是高价值 design 还是低价值 proposal。本模块 4 份 = 2 design（成文）+ 2 proposal（同源精简）。
2. **低价值 proposal 移入 `原来的文件/`**：`mv proposal-*.md 原来的文件/`（本模块已完成 2 份，归档后确认根目录剩 2 份 design）。
3. **高价值 design 用提示词整理**：用 `提示词/spec文件整理.md` 把单份 design 重构为 RAG 版（权威 0.7，按 `###` 小节切块，元数据 `doc_type=design_spec` + `source=OpenSpec`）。**只针对当前这一份做格式改造，保留原文全部业务信息，不拆分分发到外部 canonical。**
4. **收敛进语雀 canonical**：用 `提示词/spec信息补充提示题.md` 从 design 增量抽取**收敛事实**，更新 `1.语雀/` canonical（决策记录 D# / 方案选型对比 / 演进时间线 / 边界场景清单，权威 0.8）——只提取事实、不复制草稿推演。
5. **design 成文进池 0.7**：RAG 版 design 按 `###` 切进切片池 rag-slice；检索时降级处理 + 引用提示「来自历史设计文档，请核对代码确认实际落地状态」（素材库与真相源同切片池，靠 `authority=0.7` + `source=OpenSpec` 元数据识别，项目已拍板不物理隔离）。

## 三、本模块 design 关键内容（进池后供检索锚点）

- **`design-python-project-intro-rag.md`**：双池检索（索引层预写 QA 池 `doc_type=qa` + 源文档池 `doc_type=source`）/ 页面锚定（页面模式锁页 + 全局模式跨页）/ 两道门（权限门前置 + 范围门阈值：索引层 >0.75、源文档池 >0.5）/ token 真算（`stream_options.include_usage` 流结束更新 + embedding usage 单列 + 成本展示）/ 打分 `similarity × 问题类型匹配 × 页面锚定加权` / 降级矩阵（query理解/检索/打分/生成/展示 五环节）/ 追问上限 5 轮。
- **`design-python-rag-eval-agent.md`**：评测集（每模块 ≥5 条，覆盖 概览/为什么/数据流/难点/指标）/ 评测 agent（hit@k + answer_quality LLM 判分 0~5 + cost + latency）/ trace + 报告对比 / 每阶段可测试（指标纯函数 + 判分可 mock）。
