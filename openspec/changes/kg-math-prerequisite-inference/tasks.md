## 1. 创建目录结构

- [x] 1.1 创建 `edukg/core/llm_inference/` 目录
- [x] 1.2 创建 `edukg/core/llm_inference/__init__.py`
- [x] 1.3 创建 `edukg/scripts/kg_inference/` 目录

## 2. 双模型投票核心模块

- [x] 2.1 创建 `edukg/core/llm_inference/dual_model_voter.py`
- [x] 2.2 实现 `DualModelVoter` 类初始化
- [x] 2.3 实现 `vote()` 异步投票方法
- [x] 2.4 实现 `vote_prerequisite()` 前置关系投票规则
- [x] 2.5 实现 `vote_match()` 知识点匹配投票规则

## 3. LLM Prompt 模板

- [x] 3.1 创建 `edukg/core/llm_inference/prompt_templates.py`
- [x] 3.2 实现 `PREREQUISITE_PROMPT` 前置关系推断模板
- [x] 3.3 实现 `KP_MATCH_PROMPT` 知识点匹配模板
- [x] 3.4 实现 `DEFINITION_DEPS_PROMPT` 定义依赖模板（如需要）

## 4. 前置关系推断模块

- [x] 4.1 创建 `edukg/core/llm_inference/prerequisite_inferer.py`
- [x] 4.2 实现 `PrerequisiteInferer` 类
- [x] 4.3 实现 `infer_batch()` 批量推断方法
- [x] 4.4 实现 `infer_from_textbook_order()` 教材顺序推断
- [x] 4.5 实现 `extract_from_definition()` 定义依赖抽取

## 5. 配置模块

- [x] 5.1 创建 `edukg/core/llm_inference/config.py`
- [x] 5.2 配置模型名称（PRIMARY_MODEL, SECONDARY_MODEL）
- [x] 5.3 配置置信度阈值
- [x] 5.4 配置批量处理参数
- [x] 5.5 配置输出路径

## 6. 命令行入口

- [x] 6.1 创建 `edukg/scripts/kg_inference/infer_prerequisites.py`
- [x] 6.2 实现命令行参数解析
- [x] 6.3 调用 `PrerequisiteInferer` 执行推理
- [x] 6.4 输出 JSON 文件

## 7. DAG 验证

- [x] 7.1 创建 `edukg/scripts/kg_inference/validate_dag.py`
- [x] 7.2 实现有向图环检测算法
- [x] 7.3 输出验证报告

## 8. 创建输出目录

- [x] 8.1 创建 `edukg/data/edukg/math/6_推理结果/output/` 目录

## 9. 单元测试

- [x] 9.1 创建 `tests/core/llm_inference/` 测试目录
- [x] 9.2 测试 `DualModelVoter.vote()`
- [x] 9.3 测试 `DualModelVoter.vote_prerequisite()`
- [x] 9.4 测试 DAG 验证逻辑

## 10. 断点续传与缓存（集成 llmTaskLock 到 `prerequisite_inferer.py`）

- [ ] 10.1 在 `edukg/core/llm_inference/prerequisite_inferer.py` 的 `PrerequisiteInferer` 类中集成 `TaskState` 任务状态管理
- [ ] 10.2 在 `PrerequisiteInferer` 类中集成 `CachedLLM` LLM 调用缓存
- [ ] 10.3 在 `edukg/scripts/kg_inference/infer_prerequisites.py` 实现 `--resume` 断点续传参数
- [ ] 10.4 实现推理进度保存到 `progress/prerequisite_state.json`（每 N 个保存一次）
- [ ] 10.5 实现启动时加载进度文件（断点续传）
- [ ] 10.6 添加 `ProcessLock` 进程锁保护（`progress/prerequisite.lock`）

## 11. 集成测试

- [ ] 11.1 端到端测试：运行推理脚本
- [ ] 11.2 验证输出文件格式
- [ ] 11.3 验证 DAG 无环
- [ ] 11.4 测试断点续传功能（中断后恢复）
- [ ] 11.5 测试 LLM 缓存功能（相同输入复用结果）

## 12. 复用教学知识点推断（依赖 kg-math-complete-graph）

注意：`TextbookKPInferer` 类已在 `kg-math-complete-graph` 任务中实现，本模块复用。

- [ ] 12.1 确认 `kg-math-complete-graph` 已完成教学知识点推断
- [ ] 12.2 加载 `textbook_kps.json`（包含推断补全的知识点）
- [ ] 12.3 使用补全后的 TextbookKP 进行前置关系推断