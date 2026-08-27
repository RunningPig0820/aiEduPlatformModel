# 断点续传设计（集成 llmTaskLock）

> summary: 所有LLM任务支持断点续传，集成llmTaskLock的TaskState/CachedLLM/ProcessLock，匹配与推断分别用进度文件和锁文件，数据生成与精确匹配不需要。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-15-kg-math-complete-graph-D5-断点续传设计.md
> 类别：操作流程

---

### D5：断点续传设计（集成 llmTaskLock）

> 检索摘要：所有LLM任务支持断点续传，集成llmTaskLock的TaskState/CachedLLM/ProcessLock，匹配与推断分别用进度文件和锁文件，数据生成与精确匹配不需要。

**决策**: 所有 LLM 任务必须支持断点续传

**需要断点续传的任务**：

- **知识图谱匹配**
  - 核心模块：`edukg/core/textbook/kp_matcher.py`
  - 命令行入口：`match_textbook_kp.py --resume`
  - 进度文件：`progress/match_kg_state.json`
  - 锁文件：`progress/match_kg.lock`
- **教学知识点推断**
  - 核心模块：`edukg/core/llm_inference/textbook_kp_inferer.py`
  - 命令行入口：`infer_textbook_kp.py --resume`
  - 进度文件：`progress/infer_kp_state.json`
  - 锁文件：`progress/infer_kp.lock`

**不需要断点续传的任务**：
- 数据生成 (`generate_textbook_data.py`) - 纯 JSON 解析，无 LLM 调用
- 精确匹配 - 字符串比对，瞬时完成

**集成示例 (KPMatcher)**：

```python
from edukg.core.llmTaskLock import TaskState, CachedLLM, ProcessLock

class KPMatcher:
    def __init__(self):
        self.task_state = TaskState("kp_match")
        self.cached_llm = CachedLLM("kp_match_cache")
        self.process_lock = ProcessLock("kp_match.lock")

    async def match_batch(self, pairs, resume=True):
        # 加载进度
        if resume:
            completed = self.task_state.load()

        with self.process_lock:
            for pair in pairs:
                # 跳过已完成
                if pair['id'] in completed:
                    continue

                # 检查缓存
                cached = self.cached_llm.get(pair)
                if cached:
                    results.append(cached)
                    continue

                # 执行匹配
                result = await self._match_one(pair)

                # 缓存 + 记录
                self.cached_llm.set(pair, result)
                self.task_state.mark_done(pair['id'])

                # 定期保存
                if len(results) % 10 == 0:
                    self.task_state.save()

            self.task_state.save()
```

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-15-kg-math-complete-graph.md`（§D5：断点续传设计（集成 llmTaskLock））
