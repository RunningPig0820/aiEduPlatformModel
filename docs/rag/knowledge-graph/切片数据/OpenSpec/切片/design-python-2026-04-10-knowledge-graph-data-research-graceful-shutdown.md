# 13.8 Graceful Shutdown
> summary: Graceful Shutdown 监听 SIGINT/SIGTERM，中断时保存当前状态，下次可继续处理。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-graceful-shutdown.md
> 类别：开发难点

> 检索摘要：Graceful Shutdown 监听 SIGINT/SIGTERM，中断时保存当前状态，下次可继续处理。

手动中断处理：
import signal
import sys

class GracefulShutdown:
    def __init__(self, state_db):
        self.state_db = state_db
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self._handler)
        signal.signal(signal.SIGTERM, self._handler)

    def _handler(self, signum, frame):
        logging.warning(f"收到中断信号 {signum}, 准备优雅退出...")
        self.shutdown_requested = True

    def check(self) -> bool:
        """检查是否需要中断"""
        if self.shutdown_requested:
            logging.info("保存当前状态，准备退出...")
            self.state_db.save_pending_states()
            return True
        return False

def process_with_shutdown(candidates, state_db):
    shutdown = GracefulShutdown(state_db)
    for batch in candidates:
        if shutdown.check():
            logging.info("用户中断，已保存进度，下次可继续")
            sys.exit(0)
        process_batch(batch, state_db)

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.8 Graceful Shutdown）
