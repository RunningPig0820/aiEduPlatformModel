"""
真实 API 集成测试
需要配置真实 API Key
验证与各 Provider 的实际连通性
"""
import os
import pytest
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


def pytest_configure(config):
    """标记需要 API Key 的测试"""
    config.addinivalue_line(
        "markers", "requires_zhipu: 需要 ZHIPU_API_KEY"
    )
    config.addinivalue_line(
        "markers", "requires_deepseek: 需要 DEEPSEEK_API_KEY"
    )
    config.addinivalue_line(
        "markers", "requires_bailian: 需要 DASHSCOPE_API_KEY"
    )


def pytest_collection_modifyitems(config, items):
    """跳过没有 API Key 的测试"""
    skip_zhipu = pytest.mark.skip(reason="需要设置 ZHIPU_API_KEY 环境变量")
    skip_deepseek = pytest.mark.skip(reason="需要设置 DEEPSEEK_API_KEY 环境变量")
    skip_bailian = pytest.mark.skip(reason="需要设置 DASHSCOPE_API_KEY 或 BAILIAN_API_KEY 环境变量")

    for item in items:
        if "requires_zhipu" in item.keywords and not os.getenv("ZHIPU_API_KEY"):
            item.add_marker(skip_zhipu)
        if "requires_deepseek" in item.keywords and not os.getenv("DEEPSEEK_API_KEY"):
            item.add_marker(skip_deepseek)
        # 百炼支持 DASHSCOPE_API_KEY 或 BAILIAN_API_KEY
        if "requires_bailian" in item.keywords and not (os.getenv("DASHSCOPE_API_KEY") or os.getenv("BAILIAN_API_KEY")):
            item.add_marker(skip_bailian)


def get_api_key(provider: str) -> str:
    """获取指定 provider 的 API Key"""
    key_map = {
        "zhipu": "ZHIPU_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "bailian": "DASHSCOPE_API_KEY",
    }
    return os.getenv(key_map.get(provider, ""))