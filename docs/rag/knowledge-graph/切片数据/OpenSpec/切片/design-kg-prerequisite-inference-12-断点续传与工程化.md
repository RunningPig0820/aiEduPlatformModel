# 断点续传与工程化
> summary: 断点续传与工程化
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-prerequisite-inference-12-断点续传与工程化.md
> 类别：开发难点

> 检索摘要：所有LLM推断任务如何用llmTaskLock（TaskState/CachedLLM/ProcessLock）实现断点续传，哪些任务需要续传哪些不需要，进度文件与锁文件位置，缓存复用控制成本，进度文件损坏兜底。

## 设计决策

所有 LLM 推断任务必须支持断点续传，统一使用 llmTaskLock 模块。

## 需要断点续传的任务

前置关系推断：
- 核心模块：edukg/core/llm_inference/prerequisite_inferer.py
- 命令行入口：infer_prerequisites.py --resume
- 进度文件：progress/prerequisite_state.json
- 锁文件：progress/prerequisite.lock

## 不需要断点续传的任务

- 教材顺序推断（infer_from_textbook_order）：基于章节顺序，无 LLM 调用
- 定义依赖抽取（extract_from_definition）：文本解析，瞬时完成
- DAG 验证（validate_dag.py）：图算法，无 LLM 调用

## llmTaskLock 三件套

- TaskState：任务状态管理，记录已处理的知识点对 ID
- CachedLLM：LLM 调用缓存，相同输入复用结果
- ProcessLock：进程锁保护，防止多进程冲突

## 集成流程（PrerequisiteInferer 示例）

infer_batch(kp_pairs, resume=True) 的断点续传流程：
1. 加载进度：resume 时用 task_state.load() 恢复已完成的 pair_id 集合
2. 进程锁保护：with process_lock 进入临界区
3. 遍历知识点对：跳过已完成、命中 CachedLLM 缓存直接复用结果
4. 执行推断并写缓存：cached_llm.set 保存结果，task_state.mark_done 记录完成
5. 定期保存：每处理 N 个保存一次进度，结束前最终保存

配置参数：CHECKPOINT_INTERVAL = 10（每 N 个保存进度），BATCH_SIZE = 10，RATE_LIMIT_DELAY = 1.0，PROGRESS_DIR = edukg/data/edukg/math/6_推理结果/output/progress/

## 风险与缓解

- 风险：实际调用次数超过预期导致成本超支。缓解：使用免费模型为主 + 缓存复用 + 监控调用次数。
- 风险：断点续传进度文件可能损坏或丢失。缓解：定期备份 + JSON 格式易恢复。

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D5/§D7/§Risk2/§Risk4）
