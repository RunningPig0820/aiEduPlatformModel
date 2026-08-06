"""
Tutoring 真实 API 测试配置
需要配置真实 API Key, 无 key 自动 skip
"""
import os
import pytest
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


def pytest_collection_modifyitems(config, items):
    """跳过没有 API Key 的测试"""
    skip_deepseek = pytest.mark.skip(reason="需要设置 DEEPSEEK_API_KEY 环境变量")

    for item in items:
        if "requires_deepseek" in item.keywords and not os.getenv("DEEPSEEK_API_KEY"):
            item.add_marker(skip_deepseek)
