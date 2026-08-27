# D4: 任务状态接口
> summary: 统一任务状态接口 TaskState 提供 start/complete_checkpoint/resume 等方法，支撑断点续传与进度恢复。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-08-kg-infrastructure-init-D4-任务状态接口.md
> 类别：架构设计

> 检索摘要：统一任务状态接口 TaskState 提供 start/complete_checkpoint/resume 等方法，支撑断点续传与进度恢复。

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

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-08-kg-infrastructure-init.md`（§D4: 任务状态接口）
