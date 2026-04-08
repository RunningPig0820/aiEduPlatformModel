# LLM Task Lock Module

提供 LLM 任务管理的基础设施，支持断点续传、LLM 调用缓存和进程锁。

## 模块组成

| 模块 | 功能 | 文件 |
|------|------|------|
| TaskState | 任务状态管理，支持断点续传 | `state_manager.py` |
| CachedLLM | LLM 调用缓存，避免重复调用 | `llm_cache.py` |
| ProcessLock | 进程锁，防止并发冲突 | `process_lock.py` |

## 快速开始

### 1. 任务状态管理

```python
from edukg.core.llmTaskLock import TaskState

# 创建任务状态
state = TaskState("curriculum_extraction", state_dir="state/")

# 开始任务（创建15个检查点）
state.start(total=15)

# 完成检查点
state.complete_checkpoint("checkpoint_1", {"result": "..."})

# 标记失败
state.fail_checkpoint("checkpoint_2", "网络超时")

# 获取进度
progress = state.get_progress()
# {"total": 15, "completed": 1, "failed": 1, "pending": 13}

# 检查是否完成
if state.is_completed():
    print("任务已完成")

# 断点恢复
pending = state.resume()  # 返回待处理的检查点列表
```

### 2. LLM 调用缓存

```python
from edukg.core.llmTaskLock import CachedLLM
from langchain_community.chat_models import ChatZhipuAI

# 初始化
llm = ChatZhipuAI(model="glm-4-flash")
cached_llm = CachedLLM(llm, cache_dir="cache/")

# 调用（自动缓存）
result = cached_llm.invoke("解释什么是机器学习")

# 第二次调用相同提示词，直接返回缓存
result2 = cached_llm.invoke("解释什么是机器学习")  # 不调用LLM

# 不使用缓存
result3 = cached_llm.invoke("新问题", use_cache=False)

# 清理缓存
cached_llm.clear_cache(older_than=7)  # 清理7天前的缓存
```

### 3. 进程锁

```python
from edukg.core.llmTaskLock import ProcessLock

# 上下文管理器方式（推荐）
with ProcessLock("state/curriculum.lock", timeout=3600):
    # 执行任务，防止多进程冲突
    process_curriculum()

# 手动方式
lock = ProcessLock("state/curriculum.lock")
lock.acquire()
try:
    process_curriculum()
finally:
    lock.release()
```

## 状态文件结构

状态文件存储在 `state/{task_id}.json`：

```json
{
  "task_id": "curriculum_extraction",
  "created_at": "2026-04-07T10:00:00Z",
  "updated_at": "2026-04-07T10:30:00Z",
  "status": "in_progress",
  "progress": {
    "total": 15,
    "completed": 5,
    "failed": 0,
    "pending": 10
  },
  "checkpoints": [
    {
      "id": "checkpoint_1",
      "status": "completed",
      "result": {...},
      "completed_at": "2026-04-07T10:05:00Z"
    }
  ]
}
```

## 缓存文件结构

缓存文件存储在 `cache/{cache_key}.json`：

```json
{
  "cache_key": "a1b2c3d4e5f6",
  "created_at": "2026-04-07T10:00:00Z",
  "prompt": "原始提示词...",
  "result": {...}
}
```

## 设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 存储方案 | JSON 文件 | 简单、无需外部服务、便于调试 |
| 缓存键 | SHA256[:16] | 唯一性、短小、可读 |
| 进程锁 | portalocker | 跨平台、简单可靠 |

## 适用场景

| 模块 | LLM 调用次数 | 断点续传价值 |
|------|-------------|-------------|
| curriculum 知识点提取 | ~15 次 | ⭐ |
| curriculum 类型推断 | ~100+ 次 | ⭐⭐⭐ |
| curriculum 定义生成 | ~100+ 次 | ⭐⭐⭐ |
| 先修关系推断 | ~8,980 次 | ⭐⭐⭐⭐⭐ |

## 依赖

- Python 3.11+
- portalocker (进程锁)

```bash
pip install portalocker
```