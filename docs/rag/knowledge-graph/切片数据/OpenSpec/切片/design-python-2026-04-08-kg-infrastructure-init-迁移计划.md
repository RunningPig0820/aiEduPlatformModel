# Migration Plan：llmTaskLock 落地步骤
> summary: llmTaskLock 模块按 state_manager/llm_cache/process_lock 三文件落地并加 portalocker 依赖，附 TaskState/CachedLLM 使用示例。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-迁移计划.md
> 类别：操作流程

> 检索摘要：llmTaskLock 模块按 state_manager/llm_cache/process_lock 三文件落地并加 portalocker 依赖，附 TaskState/CachedLLM 使用示例。

**执行步骤**:
1. 创建 `edukg/core/llmTaskLock/__init__.py`
2. 创建 `edukg/core/llmTaskLock/state_manager.py`
3. 创建 `edukg/core/llmTaskLock/llm_cache.py`
4. 创建 `edukg/core/llmTaskLock/process_lock.py`
5. 添加 `portalocker` 依赖到 requirements.txt
6. 创建单元测试
7. 更新 curriculum 模块集成

**使用示例**:
```python
# 在 curriculum 模块中使用
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

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§Migration Plan：llmTaskLock 落地步骤）
