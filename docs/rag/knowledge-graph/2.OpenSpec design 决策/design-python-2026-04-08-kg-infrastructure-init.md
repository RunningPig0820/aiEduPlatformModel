## Context

知识图谱数据处理项目需要工程化基础设施支持断点续传和 LLM 调用管理。

### 当前状态

**curriculum 模块（课标处理）**：
- OCR 文件: 321KB（189 页）
- LLM 调用场景:
  - 知识点提取: ~15 次分块调用
  - 类型推断: ~100+ 次调用（每个知识点）
  - 定义生成: ~100+ 次调用
  - 关系提取: ~10+ 次调用
- 模型: glm-4-flash（免费）
- 问题: 中途失败需要重头开始

**后续模块（教材处理）**：
- 知识点匹配
- 先修关系推断（可能使用付费模型）

### 设计约束

- 支持 Linux/macOS/Windows 跨平台
- 支持免费和付费模型
- 锁超时防止死锁
- 简单易用，不依赖外部服务（如 Redis）

## Goals / Non-Goals

**Goals:**
- 实现任务状态管理（TaskState）
- 实现 LLM 缓存机制（LLMCache）
- 实现断点续传支持
- 实现进度显示和恢复

**Non-Goals:**
- 不实现分布式任务调度
- 不实现 Web UI
- 不实现复杂的成本监控（免费模型不需要）

## Decisions

### D1: 存储方案 - JSON 文件

**决策**: 使用 JSON 文件存储状态（不依赖 MySQL）

**理由**:
- 简单易用，无需额外服务
- 适合单机场景
- 便于调试和查看
- 课标处理任务规模不大

```python
# 状态文件结构
task_state.json = {
    "task_id": "curriculum_extraction",
    "created_at": "2026-04-07T10:00:00Z",
    "updated_at": "2026-04-07T10:30:00Z",
    "status": "in_progress",  # pending, in_progress, completed, failed
    "progress": {
        "total": 15,
        "completed": 5,
        "failed": 0
    },
    "checkpoints": [
        {
            "id": "chunk_1",
            "status": "completed",
            "result_file": "cache/chunk_1.json",
            "completed_at": "..."
        },
        {
            "id": "chunk_2",
            "status": "in_progress",
            "started_at": "..."
        }
    ]
}
```

**替代方案**: MySQL
- **优点**: 更可靠，支持并发
- **缺点**: 需要额外配置，增加复杂度

### D2: 缓存策略

**决策**: LLM 响应缓存到文件，使用 SHA256 作为键

```python
import hashlib
import json

def get_cache_key(prompt: str) -> str:
    """生成缓存键"""
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]

def save_cache(cache_key: str, result: dict, cache_dir: str = "cache/"):
    """保存缓存"""
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return str(cache_file)

def load_cache(cache_key: str, cache_dir: str = "cache/") -> Optional[dict]:
    """加载缓存"""
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    return None
```

**理由**:
- 文件缓存简单可靠
- SHA256 键保证唯一性
- 便于调试（可直接查看文件）

### D3: 进程锁实现

**决策**: 使用文件锁（portalocker）

```python
import portalocker

class ProcessLock:
    def __init__(self, lock_file: str, timeout: int = 3600):
        self.lock_file = lock_file
        self.timeout = timeout
        self.lock_fd = None

    def __enter__(self):
        self.lock_fd = open(self.lock_file, 'w')
        portalocker.lock(self.lock_fd, portalocker.LOCK_EX)
        return self

    def __exit__(self, *args):
        if self.lock_fd:
            portalocker.unlock(self.lock_fd)
            self.lock_fd.close()
```

**理由**:
- 跨平台支持
- 简单高效
- 防止多进程同时运行

### D4: 任务状态接口

**决策**: 统一的任务状态接口

```python
class TaskState:
    """任务状态管理"""

    def __init__(self, task_id: str, state_dir: str = "state/"):
        self.task_id = task_id
        self.state_file = Path(state_dir) / f"{task_id}.json"
        self._load_state()

    def start(self, total: int) -> None:
        """开始任务"""

    def complete_checkpoint(self, checkpoint_id: str, result: Any) -> None:
        """完成一个检查点"""

    def fail_checkpoint(self, checkpoint_id: str, error: str) -> None:
        """标记检查点失败"""

    def get_next_checkpoint(self) -> Optional[str]:
        """获取下一个待处理的检查点"""

    def is_completed(self) -> bool:
        """任务是否完成"""

    def get_progress(self) -> dict:
        """获取进度信息"""

    def resume(self) -> List[str]:
        """恢复未完成的检查点"""
```

### D5: LLM 调用包装器

**决策**: 带 cache 的 LLM 调用包装器

```python
class CachedLLM:
    """带缓存的 LLM 调用"""

    def __init__(self, llm, cache_dir: str = "cache/"):
        self.llm = llm
        self.cache_dir = cache_dir

    def invoke(self, prompt: str, use_cache: bool = True) -> dict:
        """调用 LLM，支持缓存"""
        cache_key = get_cache_key(prompt)

        # 尝试从缓存加载
        if use_cache:
            cached = load_cache(cache_key, self.cache_dir)
            if cached:
                return cached

        # 调用 LLM
        result = self.llm.invoke(prompt)

        # 保存缓存
        save_cache(cache_key, result, self.cache_dir)

        return result
```

## Risks / Trade-offs

### Risk 1: 文件损坏
**风险**: 状态文件损坏导致无法恢复
**缓解**: 每次更新前备份，使用原子写入

### Risk 2: 缓存过大
**风险**: 大量 LLM 调用产生大量缓存文件
**缓解**: 提供 `--clear-cache` 命令清理

### Risk 3: 锁残留
**风险**: 进程异常退出导致锁文件残留
**缓解**: 检查锁文件时间戳，超过超时自动清理

## Migration Plan

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

## Open Questions

1. 是否需要支持任务优先级？（暂不需要）
2. 是否需要支持任务依赖？（暂不需要）
3. 是否需要 Web 进度展示？（暂不需要，CLI 足够）