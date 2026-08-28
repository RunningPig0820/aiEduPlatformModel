# rag-assistant-eval Specification

## Purpose

复用 Model 仓库 `run_eval.py`/`eval_agent.py`/`eval_dataset.py` 评估链，为 RAG 项目介绍助手扩充评估能力：新增 `边界拒答` 评估类型、`precision_at_k` 精确率指标、is_quoted 纯函数校验；baseline 报告（hit@k/质量分/成本/耗时）经接口白盒展示，作为"证明系统有效"的可量化依据。

## ADDED Requirements

### Requirement: 评估集扩面

系统 SHALL 扩充 RAG 助手评估集，覆盖 5 类场景：项目介绍类、操作流程类、数据关联类、难点技术类、**边界拒答类**。每模块 ≥5 条。

#### Scenario: 评估集覆盖 5 类

- **WHEN** 加载 RAG 助手评估集
- **THEN** 用例类型覆盖 项目介绍/操作/数据关联/难点/边界拒答 五类，每类 ≥1 条、每模块 ≥5 条

#### Scenario: 格式校验

- **WHEN** 评估集含缺字段/非法类型用例
- **THEN** 加载器抛 ValueError（沿用 `eval_dataset.py` 格式校验，不静默）

### Requirement: 边界拒答类型判定

系统 SHALL 支持评估"拒答是否正确触发"：`边界拒答` 类型用例的 expected 断言 = 系统必须返回固定低置信话术且**不产生 generate token 流**（boundary 路径已付 recall，无生成）。

#### Scenario: 无语料模块低置信判定

- **WHEN** 用例指向无语料模块（如知识图谱），四模块放行 → 正常召回但命中为空
- **THEN** 评估断言命中固定低置信话术（reason=low_confidence）+ 无生成 token，判定通过

#### Scenario: 语料未覆盖低置信判定

- **WHEN** 用例为语料未覆盖的边角问题
- **THEN** 评估断言命中固定低置信话术 + 无生成 token，判定通过

### Requirement: precision_at_k 指标

系统 SHALL 提供 `precision_at_k` 纯函数：召回 top-k 中与预期引用相关块占比（相关判定沿用 expected_references 的节号匹配），纳入聚合报告。

#### Scenario: 计算精确率

- **WHEN** 给定召回 top-k 与 expected_references
- **THEN** 计算相关块占比 0~1，纳入聚合指标展示

### Requirement: is_quoted 校验入评估

系统 SHALL 将 `is_quoted` LCS 硬匹配实现为纯函数（可单测），并纳入评估：断言 `quoted_keys ⊆ 召回块集合`（引用不得指向未召回内容）。评估集 SHALL 含"改写答案"用例（LLM 改写用词后引用是否仍命中），验证 8 中文字符窗口是否足够。

#### Scenario: 引用属于召回块

- **WHEN** 某轮评估生成完成
- **THEN** 断言 quoted_keys 全部 ∈ 该轮召回块，越界即失败

#### Scenario: 改写答案引用命中

- **WHEN** 评估集含 LLM 改写用词后的答案（如原文"类型先行流式"改写为"type先行"）
- **THEN** 评估记录该块引用命中与否，用于评估 8 字符窗口漏判率（漏判 → 调窗口或加边界处理）

### Requirement: baseline 报告可复现与对比

系统 SHALL 复用 `run_eval.py` 的可复现执行与版本对比能力（`--compare`），每次语料/参数/提示词变更后重跑评测生成对比报告。

#### Scenario: 版本对比

- **WHEN** 语料或检索参数变更后重跑评测
- **THEN** 生成新版本报告，与上一份对比 hit@k/质量分/成本/耗时变化（↑/↓/=）

#### Scenario: 报告落盘

- **WHEN** 评测执行完成
- **THEN** trace 落盘 jsonl、聚合报告落盘 reports/<version>.json，结构与既有 `run_eval.py` 一致

### Requirement: 评估报告白盒展示

系统 SHALL 提供接口返回最新评估报告（hit@k/质量分/成本/耗时/judged），供 RAG 助手前端作为"证明有效"的一屏展示。

#### Scenario: 查询最新报告

- **WHEN** 前端请求评估报告
- **THEN** 系统返回最新 baseline（hit@3、质量分、avg 耗时、avg 成本、条数、版本）

#### Scenario: 无报告

- **WHEN** 尚未跑过评测
- **THEN** 返回明确的"暂无评估报告"提示，不报错
