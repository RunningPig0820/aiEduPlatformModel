"""
Pytest 配置 - 用于单元测试和集成测试（Mock）
真实 API 测试使用 tests/real/conftest.py
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


@pytest.fixture(autouse=True, scope="session")
def setup_test_env():
    """设置测试环境变量（仅用于 Mock 测试）"""
    # 为 Mock 测试设置默认值
    # 真实 API 测试会读取实际环境变量
    test_defaults = {
        "ZHIPU_API_KEY": "test_zhipu_key",
        "DEEPSEEK_API_KEY": "test_deepseek_key",
        "BAILIAN_API_KEY": "test_bailian_key",
        "DASHSCOPE_API_KEY": "test_dashscope_key",
        "INTERNAL_TOKEN": "test_internal_token",
    }

    for key, default_value in test_defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value

    yield