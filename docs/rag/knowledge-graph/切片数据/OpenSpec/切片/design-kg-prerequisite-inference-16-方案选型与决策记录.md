# 方案选型与决策记录
> summary: 方案选型与决策记录
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-prerequisite-inference-16-方案选型与决策记录.md
> 类别：架构设计

> 检索摘要：前置关系推断模块的关键设计决策：核心代码目录结构（edukg/core/llm_inference/与scripts命令行入口）、提示词文件化设计（PromptLoader支持文件与MySQL加载）、config配置（模型/投票阈值/批量/断点续传参数）与迁移实施步骤。

## 决策 D1：目录结构设计

核心代码放入 edukg/core/llm_inference/：
- __init__.py：模块导出
- config.py：配置（模型、阈值等）
- prompt_templates.py：Prompt 加载和格式化
- dual_model_voter.py：双模型投票核心逻辑
- prerequisite_inferer.py：前置关系推断
- textbook_kp_inferer.py：教学知识点推断（新增）
- README.md：模块文档
- prompts/：提示词文件目录（新增），含 prerequisite.txt（前置关系推断）、kp_match.txt（知识点匹配）、definition_deps.txt（定义依赖抽取）、textbook_kg.txt（教学知识点推断）

scripts 只做命令行入口，位于 edukg/scripts/kg_inference/：
- infer_prerequisites.py：前置关系推断入口
- infer_textbook_kp.py：教学知识点推断入口（新增）
- validate_dag.py：DAG 验证入口

## 决策 D3：提示词文件化设计

决策：提示词从代码内联改为独立文件，便于修改，并支持后续扩展从 MySQL 加载。

PromptLoader 类：
- load(name, use_cache=True)：从文件加载提示词
- _load_from_file(name)：从 prompts/{name}.txt 加载
- _load_from_db(name)：从 MySQL 加载（后续扩展）
- format(template, **kwargs)：格式化提示词

## 决策 D7：配置（config.py）

模型配置：PRIMARY_MODEL = glm-4-flash（免费），SECONDARY_MODEL = deepseek-chat（DeepSeek-V3）
投票阈值：CONFIDENCE_THRESHOLD_HIGH = 0.8，CONFIDENCE_THRESHOLD_LOW = 0.6
批量处理：BATCH_SIZE = 10，RATE_LIMIT_DELAY = 1.0
断点续传：CHECKPOINT_INTERVAL = 10（每 N 个保存进度），PROGRESS_DIR = edukg/data/edukg/math/6_推理结果/output/progress/

## 迁移计划（实施步骤）

1. 完善核心模块：创建 textbook_kp_inferer.py，集成 llmTaskLock 到推断器
2. 更新提示词：创建 prompts/ 目录，迁移提示词到独立文件
3. 开发命令行入口：更新 infer_prerequisites.py 支持 --resume，创建 infer_textbook_kp.py
4. 运行推理：先运行教学知识点推断（补全数据），再运行前置关系推断
5. 验证和导入：DAG 验证，人工验证后导入 Neo4j

## 开放问题

无（设计已确定，无遗留待决策项）。

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D1/§D3/§D7/§Migration/§Open Questions）
