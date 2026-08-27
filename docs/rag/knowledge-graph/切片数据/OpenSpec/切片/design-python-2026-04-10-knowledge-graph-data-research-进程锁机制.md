# 13.3 进程锁机制（跨平台支持）
> summary: 进程锁防止误启动多进程或意外中断后重复启动，支持 portalocker 文件锁与 MySQL 表锁两种跨平台方案。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-进程锁机制.md
> 类别：开发难点

> 检索摘要：进程锁防止误启动多进程或意外中断后重复启动，支持 portalocker 文件锁与 MySQL 表锁两种跨平台方案。

防止误启动多进程或意外中断后重复启动。

#### 13.3.1 文件锁（portalocker，推荐）
> 检索摘要：文件锁用 portalocker LOCK_EX|LOCK_NB 非阻塞获取，写入 pid，配合上下文管理器防止多进程重复运行。

# pip install portalocker

import portalocker
import os

class ProcessLock:
    def __init__(self, lock_file: str):
        self.lock_file = lock_file
        self.lock_fd = None

    def acquire(self, timeout: int = 0) -> bool:
        """获取锁"""
        self.lock_fd = open(self.lock_file, 'w')
        try:
            portalocker.lock(self.lock_fd, portalocker.LOCK_EX | portalocker.LOCK_NB)
            self.lock_fd.write(f"pid={os.getpid()}\n")
            return True
        except portalocker.LockException:
            self.lock_fd.close()
            return False

    def release(self):
        if self.lock_fd:
            portalocker.unlock(self.lock_fd)
            self.lock_fd.close()

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError("Another process is running")
        return self

    def __exit__(self, *args):
        self.release()

#### 13.3.2 MySQL 表锁（替代方案）
> 检索摘要：MySQL 分布式锁表 process_lock 记录 pid/hostname，获取时清理超时锁，防止多进程冲突并支持锁信息查询。

class MySQLLock:
    """基于 MySQL 的分布式锁"""

    def __init__(self, db: MySQLManager):
        self.db = db
        self._ensure_lock_table()

    def _ensure_lock_table(self):
        """确保锁表存在"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS process_lock (
                        lock_name VARCHAR(100) PRIMARY KEY,
                        pid INT NOT NULL,
                        hostname VARCHAR(100),
                        acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_acquired (acquired_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
            conn.commit()

    def acquire(self, lock_name: str, timeout_seconds: int = 3600) -> bool:
        """
        获取锁
        timeout_seconds: 锁超时时间（防止死锁）
        """
        import socket
        hostname = socket.gethostname()
        pid = os.getpid()

        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                # 先清理过期锁
                cursor.execute("""
                    DELETE FROM process_lock
                    WHERE lock_name = %s
                    AND acquired_at < DATE_SUB(NOW(), INTERVAL %s SECOND)
                """, (lock_name, timeout_seconds))

                # 尝试获取锁
                try:
                    cursor.execute("""
                        INSERT INTO process_lock (lock_name, pid, hostname, acquired_at)
                        VALUES (%s, %s, %s, NOW())
                    """, (lock_name, pid, hostname))
                    conn.commit()
                    return True
                except pymysql.IntegrityError:
                    # 锁已被占用
                    conn.rollback()
                    return False

    def release(self, lock_name: str):
        """释放锁"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    DELETE FROM process_lock
                    WHERE lock_name = %s AND pid = %s
                """, (lock_name, os.getpid()))
            conn.commit()

    def get_lock_info(self, lock_name: str) -> Optional[Dict]:
        """获取锁信息"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT pid, hostname, acquired_at
                    FROM process_lock
                    WHERE lock_name = %s
                """, (lock_name,))
                return cursor.fetchone()

# 使用示例
def run_pipeline_with_lock(subject: str):
    lock = MySQLLock(db)
    lock_name = f"kg_pipeline_{subject}"

    if not lock.acquire(lock_name):
        info = lock.get_lock_info(lock_name)
        raise RuntimeError(
            f"Another process is running (pid={info['pid']}, host={info['hostname']})"
        )

    try:
        # 执行流程
        process_subject(subject)
    finally:
        lock.release(lock_name)

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.3 进程锁机制（跨平台支持））
