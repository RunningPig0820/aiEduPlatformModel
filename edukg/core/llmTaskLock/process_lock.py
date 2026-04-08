"""
ProcessLock - 进程锁模块

使用文件锁防止多进程同时运行同一任务。
支持跨平台（Linux/macOS/Windows）。
"""

import os
import time
import ast
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

try:
    import portalocker
except ImportError:
    portalocker = None  # type: ignore


class ProcessLock:
    """进程锁

    使用文件锁防止多进程同时运行同一任务。
    支持上下文管理器和手动获取/释放。

    Example:
        >>> # 上下文管理器方式（推荐）
        >>> with ProcessLock("state/curriculum.lock", timeout=3600):
        ...     process_curriculum()

        >>> # 手动方式
        >>> lock = ProcessLock("state/curriculum.lock")
        >>> lock.acquire()
        >>> try:
        ...     process_curriculum()
        ... finally:
        ...     lock.release()
    """

    def __init__(self, lock_file: str, timeout: int = 3600):
        """初始化进程锁

        Args:
            lock_file: 锁文件路径
            timeout: 锁超时时间（秒），超过此时间认为锁已过期
        """
        if portalocker is None:
            raise ImportError(
                "portalocker is required for ProcessLock. "
                "Install it with: pip install portalocker"
            )

        self.lock_file = Path(lock_file)
        self.timeout = timeout
        self.lock_fd: Optional[object] = None
        self._locked = False

        # 确保锁文件目录存在
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

    def _is_stale_lock(self) -> bool:
        """检查是否存在过期的锁

        Returns:
            True 如果锁文件存在且已过期
        """
        if not self.lock_file.exists():
            return False

        try:
            # 读取锁文件中的时间戳
            content = self.lock_file.read_text(encoding="utf-8")
            if content:
                # 使用 json 解析 (更安全，且 _create_lock_content 现在使用 json)
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    # 回退到 ast.literal_eval 以兼容旧的 repr() 格式
                    data = ast.literal_eval(content)

                locked_at = data.get("locked_at")
                if locked_at:
                    locked_time = datetime.fromisoformat(locked_at.replace("Z", "+00:00"))
                    age = datetime.now(timezone.utc) - locked_time
                    if age > timedelta(seconds=self.timeout):
                        return True
        except (ValueError, SyntaxError, KeyError):
            # 无法解析，检查文件修改时间
            mtime = self.lock_file.stat().st_mtime
            age = time.time() - mtime
            if age > self.timeout:
                return True

        return False

    def _create_lock_content(self) -> str:
        """创建锁文件内容

        Returns:
            锁文件内容字符串
        """
        data = {
            "pid": os.getpid(),
            "locked_at": datetime.now(timezone.utc).isoformat(),
        }
        return json.dumps(data)

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """获取锁

        Args:
            blocking: 是否阻塞等待
            timeout: 等待超时时间（秒）

        Returns:
            True 如果成功获取锁

        Raises:
            TimeoutError: 如果 blocking=True 且超时
        """
        # 检查并清理过期锁
        if self._is_stale_lock():
            self._cleanup_stale_lock()

        # 确保目录存在
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        # 打开锁文件
        self.lock_fd = open(self.lock_file, "w", encoding="utf-8")

        try:
            if blocking:
                flags = portalocker.LOCK_EX
                if timeout:
                    flags |= portalocker.LOCK_NB
                    start_time = time.time()
                    while True:
                        try:
                            portalocker.lock(self.lock_fd, flags)
                            break
                        except portalocker.LockException:
                            if time.time() - start_time > timeout:
                                raise TimeoutError(
                                    f"Failed to acquire lock within {timeout} seconds"
                                )
                            time.sleep(0.1)
                else:
                    portalocker.lock(self.lock_fd, flags)
            else:
                portalocker.lock(self.lock_fd, portalocker.LOCK_EX | portalocker.LOCK_NB)

            # 写入锁信息
            self.lock_fd.write(self._create_lock_content())
            self.lock_fd.flush()
            os.fsync(self.lock_fd.fileno())

            self._locked = True
            return True

        except (portalocker.LockException, TimeoutError):
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            raise

    def release(self) -> None:
        """释放锁"""
        if self.lock_fd and self._locked:
            try:
                portalocker.unlock(self.lock_fd)
                self.lock_fd.close()
            finally:
                self.lock_fd = None
                self._locked = False

                # 删除锁文件
                try:
                    if self.lock_file.exists():
                        self.lock_file.unlink()
                except OSError:
                    pass

    def _cleanup_stale_lock(self) -> None:
        """清理过期锁"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except OSError:
            pass

    def __enter__(self) -> "ProcessLock":
        """上下文管理器入口"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        self.release()

    def is_locked(self) -> bool:
        """检查锁是否被持有

        Returns:
            True 如果当前实例持有锁
        """
        return self._locked

    def is_locked_by_other(self) -> bool:
        """检查锁是否被其他进程持有

        Returns:
            True 如果锁被其他进程持有（且未过期）
        """
        if not self.lock_file.exists():
            return False

        if self._is_stale_lock():
            return False

        return True