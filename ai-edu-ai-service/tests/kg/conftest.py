"""
Knowledge Graph 模块测试配置
真实 Neo4j 连接测试
"""
import os
import pytest
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def pytest_configure(config):
    """Mark tests requiring Neo4j connection."""
    config.addinivalue_line(
        "markers", "requires_neo4j: 需要 Neo4j 连接配置"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests if Neo4j is not configured."""
    skip_neo4j = pytest.mark.skip(reason="需要设置 NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD 环境变量")

    for item in items:
        if "requires_neo4j" in item.keywords:
            if not (os.getenv("NEO4J_URI") and os.getenv("NEO4J_USER") and os.getenv("NEO4J_PASSWORD")):
                item.add_marker(skip_neo4j)