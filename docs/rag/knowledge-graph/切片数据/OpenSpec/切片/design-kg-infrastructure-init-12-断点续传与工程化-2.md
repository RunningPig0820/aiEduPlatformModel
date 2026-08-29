# 断点续传与工程化（llmTaskLock 三件套实现）

> summary: 断点续传与工程化
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-kg-infrastructure-init-12-断点续传与工程化-2.md
> 类别：开发难点

llmTaskLock 三件套（TaskState/CachedLLM/ProcessLock）的核心实现设计，属 design-python-2026-04-08-kg-infrastructure-init 设计稿（权威 0.7 素材层），业务真实实现请以 canonical 真相源为准。

## D1 状态存储：JSON 文件

使用 JSON 文件存储任务状态（不依赖 MySQL）。理由：简单易用无需额外服务、适合单机场景、便于调试和查看、课标处理任务规模不大。替代方案 MySQL 更可靠支持并发，但需额外配置增加复杂度。

```python
task_state.json = {
    "task_id": "curriculum_extraction",
    "created_at": "2026-04-07T10:00:00Z",
    "updated_at": "2026-04-07T10:30:00Z",
    "status": "in_progress",  # pending, in_progress, completed, failed
    "progress": {"total": 15, "completed": 5, "failed": 0},
    "checkpoints": [
        {"id": "chunk_1", "status": "completed", "result_file": "cache/chunk_1.json", "completed_at": "..."},
        {"id": "chunk_2", "status": "in_progress", "started_at": "..."}
    ]
}
```

## D4 任务状态接口 TaskState

统一的任务状态接口，提供 start/complete_checkpoint/fail_checkpoint/get_next_checkpoint/is_completed/get_progress/resume 等方法，支撑断点续传与进度恢复。

```python
class TaskState:
    """任务状态管理"""
    def __init__(self, task_id: str, state_dir: str = "state/"): ...
    def start(self, total: int) -> None: ...
    def complete_checkpoint(self, checkpoint_id: str, result: Any) -> None: ...
    def fail_checkpoint(self, checkpoint_id: str, error: str) -> None: ...
    def get_next_checkpoint(self) -> Optional[str]: ...
    def is_completed(self) -> bool: ...
    def get_progress(self) -> dict: ...
    def resume(self) -> List[str]: ...  # 恢复未完成的检查点
```

## D2 缓存策略：SHA256 缓存键

LLM 响应缓存到文件，用 prompt 的 SHA256 前 16 位作缓存键，提供 save_cache/load_cache，保证唯一性与可调试性；文件缓存简单可靠、便于直接查看。

```python
def get_cache_key(prompt: str) -> str:
    return hashlib.sha256(prompt.encode()).hexdigest()[:16]

def save_cache(cache_key, result, cache_dir="cache/"):
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

def load_cache(cache_key, cache_dir="cache/") -> Optional[dict]:
    cache_file = Path(cache_dir) / f"{cache_key}.json"
    return json.loads(cache_file.read_text()) if cache_file.exists() else None
```

## D3 进程锁：portalocker

使用文件锁（portalocker）跨平台防止多进程同时运行，带 timeout 超时机制防死锁。

```python
import portalocker

class ProcessLock:
    def __init__(self, lock_file: str, timeout: int = 3600): ...
    def __enter__(self):
        self.lock_fd = open(self.lock_file, 'w')
        portalocker.lock(self.lock_fd, portalocker.LOCK_EX)
        return self
    def __exit__(self, *args):
        if self.lock_fd:
            portalocker.unlock(self.lock_fd)
            self.lock_fd.close()
```

## D5 LLM 调用包装器 CachedLLM

带缓存的 LLM 调用包装器：invoke(prompt, use_cache=True) 先查缓存再调模型，结果自动保存，支持 use_cache 开关。

```python
class CachedLLM:
    """带缓存的 LLM 调用"""
    def __init__(self, llm, cache_dir: str = "cache/"): ...
    def invoke(self, prompt: str, use_cache: bool = True) -> dict:
        cache_key = get_cache_key(prompt)
        if use_cache:
            cached = load_cache(cache_key, self.cache_dir)
            if cached:
                return cached
        result = self.llm.invoke(prompt)
        save_cache(cache_key, result, self.cache_dir)
        return result
```

## 工程化能力

- --resume：恢复未完成的检查点（配合 TaskState.resume）
- --clear-cache：清理大量 LLM 调用产生的缓存文件
- 状态文件更新前备份 + 原子写入，防止文件损坏无法恢复
- 锁文件时间戳超过超时自动清理，防止进程异常退出残留
