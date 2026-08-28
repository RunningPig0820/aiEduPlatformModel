> summary: 评测可观测性需求（spec）：每次评测运行落 trace（JSONL）记录 query/召回/得分/引用/usage/耗时/判分可单条回溯、报告按模块+全量聚合指标并支持语料版本对比、提供报告与 trace 读取接口供前端/命令行查看。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-python-rag-eval-agent-eval-observability.md
> 类别：数据关联

# spec-python-rag-eval-agent-eval-observability（评测可观测性需求）

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。
> ⚠️代码演进说明：真实实现以 0.8 canonical + 代码为准（代码已演进：HIT_K=5 / 判分改硬算）。

### 评测 trace
> 状态：⚠️
> 检索摘要：每次评测运行落 trace（JSONL）记录 query、检索池、召回条目+得分、hit 结果、生成答案、引用、usage、耗时、判分，可单条回溯定位问题。

系统 SHALL 为每次评测运行落 trace（JSONL），记录：query、检索池、召回条目+得分、hit 结果、生成答案、引用、usage、耗时、判分。

#### Scenario: trace 落盘

- **WHEN** 一条评测完成
- **THEN** 该条完整过程 SHALL 追加写入 trace 文件（可单条回溯定位问题）

### 评测报告
> 状态：⚠️
> 检索摘要：评测报告按模块聚合+全量聚合 hit@k/平均质量分/总成本/平均耗时，语料重新整理后再次评测可对比新旧两次指标变化并标注语料版本。

系统 SHALL 生成可观测的评测报告：按模块聚合 + 全量聚合（hit@k / 平均质量分 / 总成本 / 平均耗时），并支持与历史报告对比（语料版本差异）。

#### Scenario: 报告生成

- **WHEN** 评测运行结束
- **THEN** 报告 SHALL 输出各模块与全量的指标汇总

#### Scenario: 版本对比

- **WHEN** 语料重新整理后再次评测
- **THEN** 报告 SHALL 能对比新旧两次的 hit@k 与平均质量分变化（标注语料版本）

### 观测展示
> 状态：⚠️
> 检索摘要：提供评测报告与 trace 的读取接口供前端/命令行查看效果，请求某次评测报告返回指标汇总与按模块明细。

系统 SHALL 提供评测报告与 trace 的读取接口，供前端/命令行查看效果。

#### Scenario: 查询报告

- **WHEN** 请求某次评测报告
- **THEN** 返回该次报告的指标汇总与按模块明细
