"""
LLM Cache 单元测试

测试缓存键生成、缓存读写、缓存命中
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from edukg.core.llmTaskLock import (
    get_cache_key,
    save_cache,
    load_cache,
    clear_cache,
    CachedLLM,
)


@pytest.fixture
def temp_cache_dir(tmp_path):
    """创建临时缓存目录"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return str(cache_dir)


class TestCacheKey:
    """测试缓存键生成"""

    def test_get_cache_key(self, temp_cache_dir):
        """CACHE-001: 生成缓存键"""
        key = get_cache_key("test prompt")

        assert len(key) == 16
        assert key.isalnum()

    def test_same_prompt_same_key(self, temp_cache_dir):
        """CACHE-002: 相同提示词相同键"""
        key1 = get_cache_key("test prompt")
        key2 = get_cache_key("test prompt")

        assert key1 == key2

    def test_different_prompt_different_key(self, temp_cache_dir):
        """CACHE-003: 不同提示词不同键"""
        key1 = get_cache_key("prompt 1")
        key2 = get_cache_key("prompt 2")

        assert key1 != key2


class TestCacheReadWrite:
    """测试缓存读写"""

    def test_save_cache(self, temp_cache_dir):
        """CACHE-004: 保存缓存"""
        result = {"data": "test value"}
        cache_key = get_cache_key("test prompt")

        cache_file = save_cache(cache_key, result, temp_cache_dir)

        assert Path(cache_file).exists()
        data = json.loads(Path(cache_file).read_text(encoding="utf-8"))
        assert data["result"] == result

    def test_load_cache_exists(self, temp_cache_dir):
        """CACHE-005: 加载缓存"""
        result = {"data": "test value"}
        cache_key = get_cache_key("test prompt")
        save_cache(cache_key, result, temp_cache_dir)

        loaded = load_cache(cache_key, temp_cache_dir)

        assert loaded == result

    def test_load_cache_not_exists(self, temp_cache_dir):
        """CACHE-006: 加载不存在缓存"""
        loaded = load_cache("nonexistent_key", temp_cache_dir)

        assert loaded is None


class TestCachedLLM:
    """测试 CachedLLM"""

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        mock = MagicMock()
        mock.invoke.return_value = {"result": "llm response"}
        return mock

    def test_cache_hit(self, temp_cache_dir, mock_llm):
        """CACHE-007: 缓存命中"""
        cached_llm = CachedLLM(mock_llm, cache_dir=temp_cache_dir)

        # 第一次调用
        result1 = cached_llm.invoke("test prompt")

        # 第二次调用相同提示词
        result2 = cached_llm.invoke("test prompt")

        # LLM 只应该被调用一次
        assert mock_llm.invoke.call_count == 1
        assert result1 == result2

    def test_cache_miss(self, temp_cache_dir, mock_llm):
        """CACHE-008: 缓存未命中"""
        cached_llm = CachedLLM(mock_llm, cache_dir=temp_cache_dir)

        result = cached_llm.invoke("test prompt")

        assert mock_llm.invoke.call_count == 1
        assert result == {"result": "llm response"}

    def test_disable_cache(self, temp_cache_dir, mock_llm):
        """CACHE-009: 禁用缓存"""
        cached_llm = CachedLLM(mock_llm, cache_dir=temp_cache_dir)

        # 第一次调用
        cached_llm.invoke("test prompt")

        # 第二次调用，禁用缓存
        cached_llm.invoke("test prompt", use_cache=False)

        # LLM 应该被调用两次
        assert mock_llm.invoke.call_count == 2


class TestCacheClear:
    """测试缓存清理"""

    def test_clear_all_cache(self, temp_cache_dir):
        """CACHE-010: 清理缓存"""
        # 创建一些缓存
        save_cache(get_cache_key("prompt 1"), {"data": "1"}, temp_cache_dir)
        save_cache(get_cache_key("prompt 2"), {"data": "2"}, temp_cache_dir)

        deleted = clear_cache(temp_cache_dir)

        assert deleted == 2
        assert len(list(Path(temp_cache_dir).glob("*.json"))) == 0

    def test_clear_old_cache(self, temp_cache_dir):
        """CACHE-011: 清理指定天数缓存"""
        # 创建缓存
        save_cache(get_cache_key("prompt 1"), {"data": "1"}, temp_cache_dir)
        save_cache(get_cache_key("prompt 2"), {"data": "2"}, temp_cache_dir)

        # 清理 30 天前的缓存（应该不删除任何文件）
        deleted = clear_cache(temp_cache_dir, older_than=30)

        assert deleted == 0
        assert len(list(Path(temp_cache_dir).glob("*.json"))) == 2

    def test_load_corrupted_cache(self, temp_cache_dir):
        """CACHE-012: 缓存格式验证"""
        cache_key = "corrupted_test"

        # 写入损坏的缓存文件
        cache_file = Path(temp_cache_dir) / f"{cache_key}.json"
        cache_file.write_text("invalid json {", encoding="utf-8")

        loaded = load_cache(cache_key, temp_cache_dir)

        assert loaded is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])