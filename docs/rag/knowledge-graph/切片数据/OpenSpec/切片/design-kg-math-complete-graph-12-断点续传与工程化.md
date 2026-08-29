# 断点续传与工程化

> summary: 断点续传与工程化
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-math-complete-graph-12-断点续传与工程化.md
> 类别：开发难点

---

> 检索摘要：LLM 任务中断怎么续跑？llmTaskLock 三件套怎么用？哪些任务要断点续传、哪些不需要？

## 断点续传设计（D5）

决策：所有 LLM 任务必须支持断点续传，集成 llmTaskLock 的 TaskState / CachedLLM / ProcessLock 三件套。

需要断点续传的任务：
- 知识图谱匹配：核心模块 edukg/core/textbook/kp_matcher.py，命令行入口 match_textbook_kp.py --resume，进度文件 progress/match_kg_state.json，锁文件 progress/match_kg.lock
- 教学知识点推断：核心模块 edukg/core/llm_inference/textbook_kp_inferer.py，命令行入口 infer_textbook_kp.py --resume，进度文件 progress/infer_kp_state.json，锁文件 progress/infer_kp.lock

不需要断点续传的任务：
- 数据生成（generate_textbook_data.py）：纯 JSON 解析，无 LLM 调用
- 精确匹配：字符串比对，瞬时完成

集成示例（KPMatcher）：

```python
from edukg.core.llmTaskLock import TaskState, CachedLLM, ProcessLock

class KPMatcher:
    def __init__(self):
        self.task_state = TaskState("kp_match")
        self.cached_llm = CachedLLM("kp_match_cache")
        self.process_lock = ProcessLock("kp_match.lock")

    async def match_batch(self, pairs, resume=True):
        if resume:
            completed = self.task_state.load()
        with self.process_lock:
            for pair in pairs:
                if pair['id'] in completed:
                    continue
                cached = self.cached_llm.get(pair)
                if cached:
                    results.append(cached)
                    continue
                result = await self._match_one(pair)
                self.cached_llm.set(pair, result)
                self.task_state.mark_done(pair['id'])
                if len(results) % 10 == 0:
                    self.task_state.save()
            self.task_state.save()
```

机制说明：resume 时加载已完成进度跳过已处理条目；CachedLLM 缓存 LLM 结果避免重复调用；ProcessLock 保证多进程互斥；每 10 条定期保存进度，结束时全量保存。

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D5）
