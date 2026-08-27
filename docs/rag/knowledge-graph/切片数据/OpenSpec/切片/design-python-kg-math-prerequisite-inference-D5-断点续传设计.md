# D5：断点续传设计（集成 llmTaskLock）
> summary: 断点续传设计：所有LLM推断任务集成llmTaskLock（TaskState/CachedLLM/ProcessLock），前置关系推断用infer_prerequisites.py --resume，教材顺序推断与DAG验证无需续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-kg-math-prerequisite-inference-D5-断点续传设计.md
> 类别：数据关联

> 检索摘要：断点续传设计：所有LLM推断任务集成llmTaskLock（TaskState/CachedLLM/ProcessLock），前置关系推断用infer_prerequisites.py --resume，教材顺序推断与DAG验证无需续传。

**决策**: 所有 LLM 推断任务必须支持断点续传，使用 `llmTaskLock` 模块。

**需要断点续传的任务**：

- **前置关系推断**
  - 核心模块：`edukg/core/llm_inference/prerequisite_inferer.py`
  - 命令行入口：`infer_prerequisites.py --resume`
  - 进度文件：`progress/prerequisite_state.json`
  - 锁文件：`progress/prerequisite.lock`

**不需要断点续传的任务**：
- 教材顺序推断 (`infer_from_textbook_order`) - 基于章节顺序，无 LLM 调用
- 定义依赖抽取 (`extract_from_definition`) - 文本解析，瞬时完成
- DAG 验证 (`validate_dag.py`) - 图算法，无 LLM 调用

**注意**: 教学知识点推断 (`TextbookKPInferer`) 在 `kg-math-complete-graph` 中实现，本模块复用其输出结果。

**集成示例 (PrerequisiteInferer)**：

```python
from edukg.core.llmTaskLock import TaskState, CachedLLM, ProcessLock

class PrerequisiteInferer:
    def __init__(self, ...):
        self.task_state = TaskState("prerequisite_inference")
        self.cached_llm = CachedLLM("prerequisite_cache")
        self.process_lock = ProcessLock("prerequisite.lock")

    async def infer_batch(self, kp_pairs, resume=True):
        # 加载进度
        if resume:
            completed = self.task_state.load()

        # 进程锁保护
        with self.process_lock:
            for pair in kp_pairs:
                # 跳过已完成的
                pair_id = self._make_pair_id(pair)
                if pair_id in completed:
                    continue

                # 检查缓存
                cached = self.cached_llm.get(pair)
                if cached:
                    results.append(cached)
                    continue

                # 执行推断
                result = await self._infer_one(pair)

                # 缓存结果
                self.cached_llm.set(pair, result)

                # 记录完成
                self.task_state.mark_done(pair_id)

                # 每 N 个保存进度
                if len(results) % 10 == 0:
                    self.task_state.save()

            # 最终保存
            self.task_state.save()
```

**llmTaskLock 组件**：

| 组件 | 功能 |
|------|------|
| `TaskState` | 任务状态管理（已处理的知识点对 ID） |
| `CachedLLM` | LLM 调用缓存（相同输入复用结果） |
| `ProcessLock` | 进程锁保护（防止多进程冲突） |

> 证据：详见 `2.OpenSpec design 决策/design-python-kg-math-prerequisite-inference.md`（§D5：断点续传设计（集成 llmTaskLock））
