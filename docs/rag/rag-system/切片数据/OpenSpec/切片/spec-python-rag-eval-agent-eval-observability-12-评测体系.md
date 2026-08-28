# 评测体系（报告聚合与版本对比、观测展示）
> summary: 评测体系（报告聚合与版本对比、观测展示）：评测报告按模块+全量聚合 hit@k/平均质量分/总成本/平均耗时并支持语料版本对比，提供报告与 trace 读取接口供前端/命令行查看。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-slices/rag-system/OpenSpec/spec-python-rag-eval-agent-eval-observability-12-评测体系.md
> 类别：数据关联

---

### 评测报告
> 检索摘要：评测报告按模块聚合+全量聚合 hit@k/平均质量分/总成本/平均耗时，语料重新整理后再次评测可对比新旧两次指标变化并标注语料版本。

系统 SHALL 生成可观测的评测报告：按模块聚合 + 全量聚合（hit@k / 平均质量分 / 总成本 / 平均耗时），并支持与历史报告对比（语料版本差异）。

#### Scenario: 报告生成

- **WHEN** 评测运行结束
- **THEN** 报告 SHALL 输出各模块与全量的指标汇总

#### Scenario: 版本对比

- **WHEN** 语料重新整理后再次评测
- **THEN** 报告 SHALL 能对比新旧两次的 hit@k 与平均质量分变化（标注语料版本）

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-eval-agent-eval-observability.md`（§评测报告）

---

### 观测展示
> 检索摘要：提供评测报告与 trace 的读取接口供前端/命令行查看效果，请求某次评测报告返回指标汇总与按模块明细。

系统 SHALL 提供评测报告与 trace 的读取接口，供前端/命令行查看效果。

#### Scenario: 查询报告

- **WHEN** 请求某次评测报告
- **THEN** 返回该次报告的指标汇总与按模块明细

> 证据：详见 `2.OpenSpec design 决策/原来的文件/spec-python-rag-eval-agent-eval-observability.md`（§观测展示）
