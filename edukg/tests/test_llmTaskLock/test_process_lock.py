"""
ProcessLock 单元测试

测试锁获取、释放、超时清理
"""
import os
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from edukg.core.llmTaskLock import ProcessLock


@pytest.fixture
def temp_lock_dir(tmp_path):
    """创建临时锁目录"""
    lock_dir = tmp_path / "locks"
    lock_dir.mkdir()
    return str(lock_dir)


class TestProcessLockAcquire:
    """测试锁获取"""

    def test_acquire_lock(self, temp_lock_dir):
        """LOCK-001: 获取锁"""
        lock_file = Path(temp_lock_dir) / "test.lock"

        lock = ProcessLock(str(lock_file), timeout=60)
        lock.acquire()

        assert lock.is_locked()
        assert lock_file.exists()

        lock.release()

    def test_release_lock(self, temp_lock_dir):
        """LOCK-002: 释放锁"""
        lock_file = Path(temp_lock_dir) / "test.lock"

        lock = ProcessLock(str(lock_file), timeout=60)
        lock.acquire()
        lock.release()

        assert not lock.is_locked()
        assert not lock_file.exists()

    def test_context_manager(self, temp_lock_dir):
        """LOCK-003: 上下文管理器"""
        lock_file = Path(temp_lock_dir) / "test.lock"

        with ProcessLock(str(lock_file), timeout=60):
            assert lock_file.exists()

        assert not lock_file.exists()


class TestProcessLockTimeout:
    """测试锁超时"""

    def test_stale_lock_cleanup(self, temp_lock_dir):
        """LOCK-004: 锁超时检测"""
        lock_file = Path(temp_lock_dir) / "test.lock"

        # 创建一个"过期"的锁文件
        lock_file.write_text("{'pid': 99999, 'locked_at': '2020-01-01T00:00:00Z'}", encoding="utf-8")

        # 使用很短的超时，应该能清理过期锁
        lock = ProcessLock(str(lock_file), timeout=1)
        lock.acquire()

        assert lock.is_locked()

        lock.release()

    def test_lock_file_contains_metadata(self, temp_lock_dir):
        """LOCK-006: 锁文件包含进程信息"""
        lock_file = Path(temp_lock_dir) / "test.lock"

        with ProcessLock(str(lock_file), timeout=60):
            content = lock_file.read_text(encoding="utf-8")
            assert str(os.getpid()) in content

    def test_manual_acquire_release(self, temp_lock_dir):
        """LOCK-007: 手动获取释放"""
        lock_file = Path(temp_lock_dir) / "test.lock"

        lock = ProcessLock(str(lock_file), timeout=60)
        lock.acquire()
        assert lock.is_locked()

        lock.release()
        assert not lock.is_locked()

    def test_exception_auto_release(self, temp_lock_dir):
        """LOCK-008: 异常时自动释放"""
        lock_file = Path(temp_lock_dir) / "test.lock"

        try:
            with ProcessLock(str(lock_file), timeout=60):
                raise ValueError("test error")
        except ValueError:
            pass

        # 锁应该被释放
        assert not lock_file.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])