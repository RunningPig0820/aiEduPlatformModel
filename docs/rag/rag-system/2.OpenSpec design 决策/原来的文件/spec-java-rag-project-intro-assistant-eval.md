> summary: 本spec定义RAG项目介绍助手的评估能力：复用run_eval.py评估链，新增边界拒答评估类型、precision_at_k精确率指标、is_quoted纯函数校验，baseline报告(hit@k/质量分/成本/耗时)接口白盒展示证明系统有效。
> 权威度: 0.7
> 模块: rag-system
> COS路径: rag-source/rag-system/OpenSpec设计决策/spec-java-rag-project-intro-assistant-eval.md
> 类别：数据关联

# rag-assistant-eval Specification

## 文档说明
> 本文件为原始spec文档的RAG结构化重构版本。
> ⚠️重要提示：本文属于**设计阶段素材**，同时包含✅已落地、⚠️构想未实现、❓待决策内容；业务真实实现请以权威度0.8的canonical真相源文档为准。本文件独立完整，内容不拆分到外部canonical文档。

### 文档目的（Purpose）
> 状态：⚠️
> 检索摘要：复用Model仓库run_eval.py评估链为RAG助手扩充评估：边界拒答类型、precision_at_k精确率、is_quoted校验，baseline报告白盒展示证明系统有效。

复用 Model 仓库 `run_eval.py`/`eval_agent.py`/`eval_dataset.py` 评估链，为 RAG 项目介绍助手扩充评估能力：新增 `边界拒答` 评估类型、`precision_at_k` 精确率指标、is_quoted 纯函数校验；baseline 报告（hit@k/质量分/成本/耗时）经接口白盒展示，作为"证明系统有效"的可量化依据。

### 评估集扩面
> 状态：⚠️
> 检索摘要：RAG助手评估集扩面覆盖项目介绍/操作流程/数据关联/难点/边界拒答五类，每模块≥5条，缺字段非法类型加载抛ValueError。

系统 SHALL 扩充 RAG 助手评估集，覆盖 5 类场景：项目介绍类、操作流程类、数据关联类、难点技术类、**边界拒答类**。每模块 ≥5 条。

#### Scenario: 评估集覆盖 5 类
- **WHEN** 加载 RAG 助手评估集
- **THEN** 用例类型覆盖 项目介绍/操作/数据关联/难点/边界拒答 五类，每类 ≥1 条、每模块 ≥5 条

#### Scenario: 格式校验
- **WHEN** 评估集含缺字段/非法类型用例
- **THEN** 加载器抛 ValueError（沿用 `eval_dataset.py` 格式校验，不静默）

### 边界拒答类型判定
> 状态：⚠️
> 检索摘要：评估拒答是否正确触发：边界拒答用例断言必须返回固定低置信话术且不产生generate token流，boundary路径已付recall无生成。

系统 SHALL 支持评估"拒答是否正确触发"：`边界拒答` 类型用例的 expected 断言 = 系统必须返回固定低置信话术且**不产生 generate token 流**（boundary 路径已付 recall，无生成）。

#### Scenario: 无语料模块低置信判定
- **WHEN** 用例指向无语料模块（如知识图谱），四模块放行 → 正常召回但命中为空
- **THEN** 评估断言命中固定低置信话术（reason=low_confidence）+ 无生成 token，判定通过

#### Scenario: 语料未覆盖低置信判定
- **WHEN** 用例为语料未覆盖的边角问题
- **THEN** 评估断言命中固定低置信话术 + 无生成 token，判定通过

### precision_at_k 指标
> 状态：⚠️
> 检索摘要：提供precision_at_k纯函数：召回top-k中与预期引用相关块占比(节号匹配)，纳入聚合报告证明检索精确率。

系统 SHALL 提供 `precision_at_k` 纯函数：召回 top-k 中与预期引用相关块占比（相关判定沿用 expected_references 的节号匹配），纳入聚合报告。

#### Scenario: 计算精确率
- **WHEN** 给定召回 top-k 与 expected_references
- **THEN** 计算相关块占比 0~1，纳入聚合指标展示

### is_quoted 校验入评估
> 状态：⚠️
> 检索摘要：is_quoted LCS硬匹配纯函数纳入评估，断言quoted_keys⊆召回块集合，含改写答案用例验证8中文字符窗口是否足够。

系统 SHALL 将 `is_quoted` LCS 硬匹配实现为纯函数（可单测），并纳入评估：断言 `quoted_keys ⊆ 召回块集合`（引用不得指向未召回内容）。评估集 SHALL 含"改写答案"用例（LLM 改写用词后引用是否仍命中），验证 8 中文字符窗口是否足够。

#### Scenario: 引用属于召回块
- **WHEN** 某轮评估生成完成
- **THEN** 断言 quoted_keys 全部 ∈ 该轮召回块，越界即失败

#### Scenario: 改写答案引用命中
- **WHEN** 评估集含 LLM 改写用词后的答案（如原文"类型先行流式"改写为"type先行"）
- **THEN** 评估记录该块引用命中与否，用于评估 8 字符窗口漏判率（漏判 → 调窗口或加边界处理）

### baseline 报告可复现与对比
> 状态：⚠️
> 检索摘要：复用run_eval.py可复现执行与版本对比(--compare)，语料/参数/提示词变更后重跑生成对比报告，trace落jsonl报告落reports/version.json。

系统 SHALL 复用 `run_eval.py` 的可复现执行与版本对比能力（`--compare`），每次语料/参数/提示词变更后重跑评测生成对比报告。

#### Scenario: 版本对比
- **WHEN** 语料或检索参数变更后重跑评测
- **THEN** 生成新版本报告，与上一份对比 hit@k/质量分/成本/耗时变化（↑/↓/=）

#### Scenario: 报告落盘
- **WHEN** 评测执行完成
- **THEN** trace 落盘 jsonl、聚合报告落盘 reports/<version>.json，结构与既有 `run_eval.py` 一致

### 评估报告白盒展示
> 状态：⚠️
> 检索摘要：提供接口返回最新评估报告(hit@k/质量分/成本/耗时/judged)供前端一屏展示证明有效，未跑评测返回暂无评估报告不报错。

系统 SHALL 提供接口返回最新评估报告（hit@k/质量分/成本/耗时/judged），供 RAG 助手前端作为"证明有效"的一屏展示。

#### Scenario: 查询最新报告
- **WHEN** 前端请求评估报告
- **THEN** 系统返回最新 baseline（hit@3、质量分、avg 耗时、avg 成本、条数、版本）

#### Scenario: 无报告
- **WHEN** 尚未跑过评测
- **THEN** 返回明确的"暂无评估报告"提示，不报错
