"""
LLM Task Lock Module

提供 LLM 任务管理基础设施：
- TaskState: 任务状态管理，支持断点续传
- CachedLLM: LLM 调用缓存，避免重复调用
- ProcessLock: 进程锁，防止并发冲突

Example:
    >>> from edukg.core.llmTaskLock import TaskState, CachedLLM, ProcessLock
    >>>
    >>> # 任务状态管理
    >>> state = TaskState("curriculum_extraction")
    >>> state.start(total=15)
    >>> state.complete_checkpoint("chunk_1", {"result": "..."})
    >>>
    >>> # LLM 缓存
    >>> from langchain_community.chat_models import ChatZhipuAI
    >>> llm = CachedLLM(ChatZhipuAI(model="glm-4-flash"))
    >>> result = llm.invoke("解释机器学习")  # 自动缓存
    >>>
    >>> # 进程锁
    >>> with ProcessLock("state/curriculum.lock"):
    ...     process_curriculum()
"""

from edukg.core.llmTaskLock.state_manager import TaskState
from edukg.core.llmTaskLock.llm_cache import (
    CachedLLM,
    get_cache_key,
    save_cache,
    load_cache,
    clear_cache,
)
from edukg.core.llmTaskLock.process_lock import ProcessLock

__all__ = [
    # 状态管理
    "TaskState",
    # LLM 缓存
    "CachedLLM",
    "get_cache_key",
    "save_cache",
    "load_cache",
    "clear_cache",
    # 进程锁
    "ProcessLock",
]

__version__ = "1.0.0"