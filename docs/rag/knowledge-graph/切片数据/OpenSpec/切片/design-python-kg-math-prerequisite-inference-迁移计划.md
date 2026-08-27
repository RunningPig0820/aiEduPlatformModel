# Migration Plan 迁移计划
> summary: 迁移计划：完善核心模块、更新提示词、开发命令行入口，先运行知识点推断再运行前置推断，最后DAG验证与人工导入。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-迁移计划.md
> 类别：数据关联

> 检索摘要：迁移计划：完善核心模块、更新提示词、开发命令行入口，先运行知识点推断再运行前置推断，最后DAG验证与人工导入。

**执行步骤**:

1. **完善核心模块**:
   - 创建 `textbook_kp_inferer.py`
   - 集成 `llmTaskLock` 到推断器

2. **更新提示词**:
   - 创建 `prompts/` 目录
   - 迁移提示词到独立文件

3. **开发命令行入口**:
   - 更新 `infer_prerequisites.py` 支持 `--resume`
   - 创建 `infer_textbook_kp.py`

4. **运行推理**:
   - 先运行教学知识点推断（补全数据）
   - 再运行前置关系推断

5. **验证和导入**:
   - DAG 验证
   - 人工验证后导入 Neo4j

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§Migration Plan 迁移计划）
