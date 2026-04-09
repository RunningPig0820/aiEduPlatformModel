"""
LLM Cache - LLM 调用缓存模块

支持 LLM 响应缓存，避免重复调用。
使用 SHA256 哈希作为缓存键，JSON 文件存储。
"""
import hashlib
import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union

# 默认缓存目录
DEFAULT_CACHE_DIR = Path(__file__).parent.parent.parent / "cache"


def get_cache_key(prompt: str) -> str:
    """生成缓存键

    使用 SHA256 哈希的前16位作为缓存键。

    Args:
        prompt: LLM 提示词

    Returns:
        16位哈希字符串
    """
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def save_cache(
    cache_key: str,
    result: Any,
    cache_dir: Union[str, Path] = None,
    prompt: Optional[str] = None
) -> str:
    """保存缓存到文件

    Args:
        cache_key: 缓存键
        result: 要缓存的结果
        cache_dir: 缓存目录
        prompt: 原始提示词（可选，用于调试）

    Returns:
        缓存文件路径
    """
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    cache_file = cache_path / f"{cache_key}.json"

    cache_data = {
        "cache_key": cache_key,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }

    if prompt:
        cache_data["prompt"] = prompt

    cache_file.write_text(
        json.dumps(cache_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return str(cache_file)


def load_cache(
    cache_key: str,
    cache_dir: Union[str, Path] = None,
    cache_ttl: Optional[int] = None
) -> Optional[Any]:
    """从文件加载缓存

    Args:
        cache_key: 缓存键
        cache_dir: 缓存目录
        cache_ttl: 缓存有效期（秒），None 表示永不过期

    Returns:
        缓存的结果，如果不存在或已过期则返回 None
    """
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_file = Path(cache_dir) / f"{cache_key}.json"

    if not cache_file.exists():
        return None

    try:
        cache_data = json.loads(cache_file.read_text(encoding="utf-8"))

        # 检查过期时间
        if cache_ttl is not None:
            created_at_str = cache_data.get("created_at")
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - created_at).total_seconds()
                if age > cache_ttl:
                    return None

        return cache_data.get("result")
    except (json.JSONDecodeError, IOError, ValueError):
        # 缓存文件损坏或格式错误
        return None


def clear_cache(cache_dir: Union[str, Path] = None, older_than: Optional[int] = None) -> int:
    """清理缓存文件

    Args:
        cache_dir: 缓存目录
        older_than: 只清理 N 天前的缓存，None 表示清理全部

    Returns:
        删除的文件数量
    """
    cache_dir = cache_dir or DEFAULT_CACHE_DIR
    cache_path = Path(cache_dir)

    if not cache_path.exists():
        return 0

    deleted_count = 0
    now = datetime.now(timezone.utc)

    for cache_file in cache_path.glob("*.json"):
        try:
            # 读取缓存文件的创建时间
            cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
            created_at_str = cache_data.get("created_at")

            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            else:
                # 使用文件修改时间
                mtime = cache_file.stat().st_mtime
                created_at = datetime.fromtimestamp(mtime, tz=timezone.utc)

            # 检查是否需要删除
            should_delete = False
            if older_than is None:
                should_delete = True
            else:
                age = now - created_at
                if age > timedelta(days=older_than):
                    should_delete = True

            if should_delete:
                cache_file.unlink()
                deleted_count += 1

        except (json.JSONDecodeError, IOError, ValueError):
            # 文件损坏或无法读取，直接删除
            cache_file.unlink()
            deleted_count += 1

    return deleted_count


class CachedLLM:
    """带缓存的 LLM 调用包装器

    自动缓存 LLM 响应，避免重复调用相同的提示词。

    Example:
        >>> from langchain_community.chat_models import ChatZhipuAI
        >>> llm = ChatZhipuAI(model="glm-4-flash")
        >>> cached_llm = CachedLLM(llm)
        >>> result = cached_llm.invoke("请解释什么是机器学习")
        >>> # 第二次调用相同提示词会直接返回缓存
        >>> result2 = cached_llm.invoke("请解释什么是机器学习")
    """

    def __init__(self, llm: Any, cache_dir: Union[str, Path] = None):
        """初始化缓存 LLM

        Args:
            llm: LangChain LLM 实例
            cache_dir: 缓存目录
        """
        self.llm = llm
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR

    def invoke(
        self,
        prompt: str,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Any:
        """调用 LLM，支持缓存

        Args:
            prompt: 提示词
            use_cache: 是否使用缓存，默认 True
            cache_ttl: 缓存有效期（秒），None 表示永不过期

        Returns:
            LLM 响应结果
        """
        cache_key = get_cache_key(prompt)

        # 尝试从缓存加载
        if use_cache:
            cached_result = load_cache(cache_key, self.cache_dir, cache_ttl=cache_ttl)
            if cached_result is not None:
                return cached_result

        # 调用 LLM
        result = self.llm.invoke(prompt)

        # 保存缓存 - 只保存 content 字符串，而不是整个 AIMessage 对象
        if hasattr(result, 'content'):
            cache_content = result.content
        else:
            cache_content = str(result)

        save_cache(cache_key, cache_content, self.cache_dir, prompt=prompt)

        return cache_content

    def clear_cache(self, older_than: Optional[int] = None) -> int:
        """清理缓存

        Args:
            older_than: 只清理 N 天前的缓存，None 表示清理全部

        Returns:
            删除的文件数量
        """
        return clear_cache(self.cache_dir, older_than=older_than)