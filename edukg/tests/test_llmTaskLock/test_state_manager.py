"""
TaskState 单元测试

测试状态保存、加载、断点恢复、进度查询
"""
import json
import pytest
from pathlib import Path

from edukg.core.llmTaskLock import TaskState


@pytest.fixture
def temp_state_dir(tmp_path):
    """创建临时状态目录"""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return str(state_dir)


class TestTaskStateInit:
    """测试 TaskState 初始化"""

    def test_new_task_state(self, temp_state_dir):
        """STATE-001: 新建任务状态"""
        state = TaskState("test_task", state_dir=temp_state_dir)

        assert state.task_id == "test_task"
        assert state.get_status() == TaskState.STATUS_PENDING
        assert state.state_file.exists()

    def test_load_existing_state(self, temp_state_dir):
        """STATE-010: 状态持久化"""
        # 创建第一个状态
        state1 = TaskState("test_task", state_dir=temp_state_dir)
        state1.start(total=5)
        state1.complete_checkpoint("checkpoint_1", {"result": "test"})

        # 加载已有状态
        state2 = TaskState("test_task", state_dir=temp_state_dir)

        assert state2.get_status() == TaskState.STATUS_IN_PROGRESS
        progress = state2.get_progress()
        assert progress["completed"] == 1


class TestTaskLifecycle:
    """测试任务生命周期"""

    def test_start_task(self, temp_state_dir):
        """STATE-002: 开始任务"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)

        assert state.get_status() == TaskState.STATUS_IN_PROGRESS
        progress = state.get_progress()
        assert progress["total"] == 5
        assert progress["pending"] == 5
        assert progress["completed"] == 0

    def test_complete_checkpoint(self, temp_state_dir):
        """STATE-003: 完成检查点"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)
        state.complete_checkpoint("checkpoint_1", {"result": "test"})

        progress = state.get_progress()
        assert progress["completed"] == 1
        assert progress["pending"] == 4

    def test_fail_checkpoint(self, temp_state_dir):
        """STATE-004: 失败检查点"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)
        state.fail_checkpoint("checkpoint_1", "error message")

        progress = state.get_progress()
        assert progress["failed"] == 1
        assert progress["pending"] == 4


class TestProgressQuery:
    """测试进度查询"""

    def test_get_progress(self, temp_state_dir):
        """STATE-005: 获取进度"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)
        state.complete_checkpoint("checkpoint_1", {"result": "test"})
        state.fail_checkpoint("checkpoint_2", "error")

        progress = state.get_progress()
        assert progress["total"] == 5
        assert progress["completed"] == 1
        assert progress["failed"] == 1
        assert progress["pending"] == 3

    def test_is_completed_true(self, temp_state_dir):
        """STATE-006: 任务完成"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=2)
        state.complete_checkpoint("checkpoint_1", {})
        state.complete_checkpoint("checkpoint_2", {})

        assert state.is_completed() is True

    def test_is_completed_false(self, temp_state_dir):
        """STATE-007: 任务未完成"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)

        assert state.is_completed() is False

    def test_get_next_checkpoint(self, temp_state_dir):
        """STATE-008: 获取下一个检查点"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)
        state.complete_checkpoint("checkpoint_1", {})

        next_id = state.get_next_checkpoint()
        assert next_id == "checkpoint_2"


class TestResume:
    """测试断点恢复"""

    def test_resume_pending(self, temp_state_dir):
        """STATE-009: 恢复任务"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)
        state.complete_checkpoint("checkpoint_1", {})
        state.fail_checkpoint("checkpoint_2", "error")

        pending = state.resume()
        # resume() 返回 pending + failed 的检查点
        # checkpoint_2 (failed) + checkpoint_3, checkpoint_4, checkpoint_5 (pending) = 4
        assert len(pending) == 4
        assert "checkpoint_2" in pending  # failed 也应该恢复
        assert "checkpoint_3" in pending

    def test_resume_completed(self, temp_state_dir):
        """恢复已完成任务"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=2)
        state.complete_checkpoint("checkpoint_1", {})
        state.complete_checkpoint("checkpoint_2", {})

        pending = state.resume()
        assert len(pending) == 0


class TestAtomicWrite:
    """测试原子写入"""

    def test_atomic_write(self, temp_state_dir):
        """STATE-011: 原子写入"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)

        # 验证文件内容完整
        content = state.state_file.read_text(encoding="utf-8")
        data = json.loads(content)

        assert data["task_id"] == "test_task"
        assert data["status"] == TaskState.STATUS_IN_PROGRESS

    def test_backup_on_update(self, temp_state_dir):
        """STATE-012: 状态备份"""
        state = TaskState("test_task", state_dir=temp_state_dir)
        state.start(total=5)
        state.complete_checkpoint("checkpoint_1", {})

        # 检查是否有备份文件
        backup_files = list(Path(temp_state_dir).glob("test_task_backup_*.json"))
        assert len(backup_files) >= 1  # 至少有一个备份


if __name__ == "__main__":
    pytest.main([__file__, "-v"])