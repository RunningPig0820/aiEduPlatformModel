# 断点续传与工程化（llmTaskLock 落地与使用）

> summary: 断点续传与工程化
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-infrastructure-init-12-断点续传与工程化-3.md
> 类别：开发难点

llmTaskLock 模块的落地步骤与使用方式，属 design-python-2026-04-08-kg-infrastructure-init 设计稿（权威 0.7 素材层），业务真实实现请以 canonical 真相源为准。

## Migration Plan：llmTaskLock 落地步骤

1. 创建 `edukg/core/llmTaskLock/__init__.py`
2. 创建 `edukg/core/llmTaskLock/state_manager.py`
3. 创建 `edukg/core/llmTaskLock/llm_cache.py`
4. 创建 `edukg/core/llmTaskLock/process_lock.py`
5. 添加 `portalocker` 依赖到 requirements.txt
6. 创建单元测试
7. 更新 curriculum 模块集成

## 使用示例

```python
from edukg.core.llmTaskLock import TaskState, CachedLLM, ProcessLock

# 创建任务状态
state = TaskState("curriculum_extraction")

# 恢复或开始
if state.is_completed():
    print("任务已完成")
else:
    pending = state.resume()
    print(f"待处理: {pending}")

# LLM 调用带缓存
llm = CachedLLM(ChatZhipuAI(...))
result = llm.invoke(prompt)  # 自动缓存

# 进程锁
with ProcessLock("state/curriculum.lock"):
    process_curriculum()
```

## Open Questions

1. 是否需要支持任务优先级？（暂不需要）
2. 是否需要支持任务依赖？（暂不需要）
3. 是否需要 Web 进度展示？（暂不需要，CLI 足够）
