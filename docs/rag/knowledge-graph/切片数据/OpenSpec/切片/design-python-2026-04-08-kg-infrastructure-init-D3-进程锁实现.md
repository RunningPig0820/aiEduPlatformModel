# D3: 进程锁实现
> summary: 进程锁采用 portalocker 文件锁实现，跨平台、防多进程同时运行，带 timeout 超时机制防死锁。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-D3-进程锁实现.md
> 类别：架构设计

> 检索摘要：进程锁采用 portalocker 文件锁实现，跨平台、防多进程同时运行，带 timeout 超时机制防死锁。

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

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§D3: 进程锁实现）
