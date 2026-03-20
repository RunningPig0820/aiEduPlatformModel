"""
Pytest 配置
"""
import pytest
import os


@pytest.fixture(autouse=True)
def setup_env():
    """设置测试环境变量"""
    os.environ["ZHIPU_API_KEY"] = "test_zhipu_key"
    os.environ["DEEPSEEK_API_KEY"] = "test_deepseek_key"
    os.environ["BAILIAN_API_KEY"] = "test_bailian_key"
    os.environ["INTERNAL_TOKEN"] = "test_internal_token"
    yield
    # 清理
    for key in ["ZHIPU_API_KEY", "DEEPSEEK_API_KEY", "BAILIAN_API_KEY", "INTERNAL_TOKEN"]:
        if key in os.environ:
            del os.environ[key]