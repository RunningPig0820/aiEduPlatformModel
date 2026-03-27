"""
Pytest 全局配置

测试目录结构：
tests/
├── llm/           # LLM Gateway 模块测试
│   ├── unit/      # 单元测试 (Mock)
│   ├── integration/ # 集成测试 (Mock)
│   └── real/      # 真实 API 测试
└── kg/            # Knowledge Graph 模块测试
    └── real/      # 真实 Neo4j 测试
"""
import pytest
import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def pytest_configure(config):
    """配置 pytest markers."""
    config.addinivalue_line(
        "markers", "requires_zhipu: 需要 ZHIPU_API_KEY"
    )
    config.addinivalue_line(
        "markers", "requires_deepseek: 需要 DEEPSEEK_API_KEY"
    )
    config.addinivalue_line(
        "markers", "requires_bailian: 需要 DASHSCOPE_API_KEY"
    )
    config.addinivalue_line(
        "markers", "requires_neo4j: 需要 Neo4j 连接配置"
    )


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