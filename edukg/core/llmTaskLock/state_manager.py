"""
TaskState - 任务状态管理

支持断点续传、进度查询、任务恢复。
使用 JSON 文件存储状态，不依赖外部服务。
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# 默认状态目录
DEFAULT_STATE_DIR = Path(__file__).parent.parent.parent / "state"


class TaskState:
    """任务状态管理类

    支持任务的生命周期管理：
    - 创建任务状态文件
    - 管理检查点进度
    - 支持断点恢复
    - 状态持久化（JSON 文件）

    Example:
        >>> state = TaskState("curriculum_extraction")
        >>> state.start(total=15)
        >>> state.complete_checkpoint("chunk_1", {"result": "..."})
        >>> progress = state.get_progress()
        >>> if not state.is_completed():
        ...     pending = state.resume()
    """

    # 任务状态常量
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    # 检查点状态常量
    CHECKPOINT_PENDING = "pending"
    CHECKPOINT_IN_PROGRESS = "in_progress"
    CHECKPOINT_COMPLETED = "completed"
    CHECKPOINT_FAILED = "failed"

    def __init__(self, task_id: str, state_dir: Union[str, Path] = None):
        """初始化任务状态

        Args:
            task_id: 任务唯一标识符
            state_dir: 状态文件存储目录
        """
        self.task_id = task_id
        self.state_dir = Path(state_dir or DEFAULT_STATE_DIR)
        self.state_file = self.state_dir / f"{task_id}.json"

        # 确保目录存在
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # 加载或创建状态
        self._state: Dict[str, Any] = {}
        self._load_state()

    def _load_state(self) -> None:
        """加载现有状态文件，或创建新的状态"""
        if self.state_file.exists():
            try:
                self._state = json.loads(self.state_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                # 文件损坏，创建新状态
                self._create_new_state()
        else:
            self._create_new_state()

    def _create_new_state(self) -> None:
        """创建新的任务状态"""
        now = datetime.now(timezone.utc).isoformat()
        self._state = {
            "task_id": self.task_id,
            "created_at": now,
            "updated_at": now,
            "status": self.STATUS_PENDING,
            "progress": {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "pending": 0,
            },
            "checkpoints": [],
        }
        self._save_state()

    def _save_state(self) -> None:
        """保存状态到文件（原子写入）"""
        self._state["updated_at"] = datetime.now(timezone.utc).isoformat()

        # 先备份现有文件
        if self.state_file.exists():
            backup_file = self.state_dir / f"{self.task_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(self.state_file, backup_file)

        # 原子写入：先写临时文件，再重命名
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self.state_dir,
            prefix=f"{self.task_id}_tmp_",
            suffix=".json",
            delete=False,
        )
        try:
            json.dump(self._state, temp_file, ensure_ascii=False, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_file.close()
            # 重命名到最终文件
            shutil.move(temp_file.name, self.state_file)
        except Exception:
            # 清理临时文件
            temp_file.close()
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise

    def start(self, total: int) -> None:
        """开始任务

        Args:
            total: 总检查点数量
        """
        now = datetime.now(timezone.utc).isoformat()

        # 创建检查点列表
        checkpoints = []
        for i in range(total):
            checkpoints.append({
                "id": f"checkpoint_{i + 1}",
                "status": self.CHECKPOINT_PENDING,
                "started_at": None,
                "completed_at": None,
                "result_file": None,
                "error": None,
            })

        self._state["status"] = self.STATUS_IN_PROGRESS
        self._state["started_at"] = now
        self._state["progress"] = {
            "total": total,
            "completed": 0,
            "failed": 0,
            "pending": total,
        }
        self._state["checkpoints"] = checkpoints

        self._save_state()

    def complete_checkpoint(self, checkpoint_id: str, result: Any = None) -> None:
        """完成一个检查点

        Args:
            checkpoint_id: 检查点ID
            result: 结果数据（可选）
        """
        now = datetime.now(timezone.utc).isoformat()

        for checkpoint in self._state["checkpoints"]:
            if checkpoint["id"] == checkpoint_id:
                checkpoint["status"] = self.CHECKPOINT_COMPLETED
                checkpoint["completed_at"] = now
                checkpoint["result"] = result
                break

        # 更新进度
        self._update_progress()
        self._save_state()

    def fail_checkpoint(self, checkpoint_id: str, error: str) -> None:
        """标记检查点失败

        Args:
            checkpoint_id: 检查点ID
            error: 错误信息
        """
        now = datetime.now(timezone.utc).isoformat()

        for checkpoint in self._state["checkpoints"]:
            if checkpoint["id"] == checkpoint_id:
                checkpoint["status"] = self.CHECKPOINT_FAILED
                checkpoint["completed_at"] = now
                checkpoint["error"] = error
                break

        # 更新进度
        self._update_progress()
        self._save_state()

    def _update_progress(self) -> None:
        """更新进度统计"""
        total = len(self._state["checkpoints"])
        completed = sum(1 for c in self._state["checkpoints"] if c["status"] == self.CHECKPOINT_COMPLETED)
        failed = sum(1 for c in self._state["checkpoints"] if c["status"] == self.CHECKPOINT_FAILED)
        pending = total - completed - failed

        self._state["progress"] = {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
        }

        # 检查任务是否完成
        if pending == 0 and self._state["status"] == self.STATUS_IN_PROGRESS:
            if failed > 0:
                self._state["status"] = self.STATUS_FAILED
            else:
                self._state["status"] = self.STATUS_COMPLETED
            self._state["finished_at"] = datetime.now(timezone.utc).isoformat()

    def get_next_checkpoint(self) -> Optional[str]:
        """获取下一个待处理的检查点ID

        Returns:
            下一个pending状态的检查点ID，如果没有则返回None
        """
        for checkpoint in self._state["checkpoints"]:
            if checkpoint["status"] == self.CHECKPOINT_PENDING:
                return checkpoint["id"]
        return None

    def is_completed(self) -> bool:
        """检查任务是否已完成

        Returns:
            True 如果所有检查点都已完成（无pending和in_progress）
        """
        return self._state["status"] == self.STATUS_COMPLETED

    def get_progress(self) -> Dict[str, int]:
        """获取进度信息

        Returns:
            包含 total, completed, failed, pending 的字典
        """
        return self._state["progress"].copy()

    def resume(self) -> List[str]:
        """恢复未完成的检查点

        Returns:
            所有pending和failed状态的检查点ID列表
        """
        pending_ids = []
        for checkpoint in self._state["checkpoints"]:
            if checkpoint["status"] in (self.CHECKPOINT_PENDING, self.CHECKPOINT_FAILED):
                pending_ids.append(checkpoint["id"])
        return pending_ids

    def get_status(self) -> str:
        """获取任务状态

        Returns:
            任务状态字符串
        """
        return self._state["status"]

    def get_state(self) -> Dict[str, Any]:
        """获取完整状态数据

        Returns:
            完整的状态字典
        """
        return self._state.copy()

    def reset(self) -> None:
        """重置任务状态"""
        self._create_new_state()