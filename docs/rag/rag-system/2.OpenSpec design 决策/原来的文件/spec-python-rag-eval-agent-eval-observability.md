## ADDED Requirements

### Requirement: 评测 trace

系统 SHALL 为每次评测运行落 trace（JSONL），记录：query、检索池、召回条目+得分、hit 结果、生成答案、引用、usage、耗时、判分。

#### Scenario: trace 落盘

- **WHEN** 一条评测完成
- **THEN** 该条完整过程 SHALL 追加写入 trace 文件（可单条回溯定位问题）

### Requirement: 评测报告

系统 SHALL 生成可观测的评测报告：按模块聚合 + 全量聚合（hit@k / 平均质量分 / 总成本 / 平均耗时），并支持与历史报告对比（语料版本差异）。

#### Scenario: 报告生成

- **WHEN** 评测运行结束
- **THEN** 报告 SHALL 输出各模块与全量的指标汇总

#### Scenario: 版本对比

- **WHEN** 语料重新整理后再次评测
- **THEN** 报告 SHALL 能对比新旧两次的 hit@k 与平均质量分变化（标注语料版本）

### Requirement: 观测展示

系统 SHALL 提供评测报告与 trace 的读取接口，供前端/命令行查看效果。

#### Scenario: 查询报告

- **WHEN** 请求某次评测报告
- **THEN** 返回该次报告的指标汇总与按模块明细
