# 前置依赖与学习路径
> summary: 前置依赖与学习路径
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-prerequisite-inference-07-前置依赖与学习路径.md
> 类别：数据关联

> 检索摘要：前置关系推断如何区分教学顺序TEACHES_BEFORE与学习依赖PREREQUISITE，多证据（教材章节顺序/定义文本依赖/LLM双模型投票）如何融合生成前置关系，置信度阈值与候选保留规则是什么，输出哪些文件并如何做DAG环检测。

## 业务背景与设计约束

前置关系推断是知识图谱项目的核心设计成本部分。需要严格区分教学顺序（TEACHES_BEFORE）和学习依赖（PREREQUISITE），通过多证据融合生成高质量的前置关系数据。

设计约束：
- 区分教学顺序 vs 学习依赖
- 使用多模型投票提高准确率
- 保留低置信度关系作为候选
- 所有 LLM 任务必须支持断点续传
- 核心代码放入 edukg/core/llm_inference/，scripts 只做命令行入口

当前状态（设计前提）：
- 知识点：已导入 EduKG 数据（Class 39，Concept 1,295，Statement 2,932）
- 原生关系：已导入 RELATED_TO 10,183、SUB_CLASS_OF 38、PART_OF 298、BELONGS_TO 619
- LLM Gateway：支持 GLM-4-flash（免费）和 DeepSeek-V3（低成本）
- 教材数据：已生成 TextbookKP 299 个（小学47 + 初中252）

## 目标与非目标

目标：
- 基于教材章节顺序推断 TEACHES_BEFORE
- 从定义文本抽取定义依赖
- LLM 多模型投票推断 PREREQUISITE
- 从教材章节推断教学知识点（补全缺失数据）
- 融合多证据来源
- 输出 JSON 文件（手动验证后导入）
- 支持 LLM 任务断点续传

非目标：
- 不处理其他学科（物理/化学等）
- 不做人工审核（Demo 阶段自动化）
- 不处理高中数据（知识点数据源缺失）

## 双模型投票机制（PREREQUISITE 的 LLM 证据来源）

DualModelVoter 双模型投票器：主模型 glm-4-flash + 副模型 deepseek-chat，返回 consensus / result / confidence；支持依赖注入 llm_gateway。核心方法 vote(prompt) 让两模型对同一提示词独立投票，输出是否一致、投票结果、置信度、主模型响应、副模型响应。

投票规则：
- 两模型结果一致，置信度大于等于 0.8：状态为 PREREQUISITE，采纳为前置关系
- 两模型结果一致，置信度小于 0.8：状态为 PREREQUISITE_CANDIDATE，保留为候选关系
- 两模型结果不一致：不采纳

置信度阈值由配置常量控制（CONFIDENCE_THRESHOLD_HIGH=0.8、CONFIDENCE_THRESHOLD_LOW=0.6）。

## 多证据融合与输出文件

前置关系由三类证据融合产生，输出到 edukg/data/edukg/math/6_推理结果/output/：
- teaches_before.json：按教材章节顺序推断的 TEACHES_BEFORE 教学顺序关系
- definition_deps.json：从定义文本抽取的定义依赖
- llm_prereq.json：LLM 双模型投票推断的前置关系
- textbook_kps_inferred.json：推断补全的教学知识点
- final_prereq.json：融合后的最终前置关系
- validation_report.json：DAG 验证报告
- progress/：进度文件目录（prerequisite_state.json、textbook_kp_state.json、*.lock）

## 风险与缓解

- 风险：LLM 可能错误推断前置关系或教学知识点。缓解：多模型投票 + 置信度阈值 + 候选关系保留 + 人工验证。
- 风险：前置关系可能形成循环依赖环。缓解：输出后 DAG 验证 + 发现环时报警。

## 落地运行顺序

运行推理时，先运行教学知识点推断补全数据，再运行前置关系推断；输出后进行 DAG 验证，人工验证通过后导入 Neo4j。

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§Context/§Goals/§D2/§D6/§Risk1/§Risk3/§Migration）
