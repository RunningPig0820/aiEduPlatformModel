#!/usr/bin/env python
"""
create_neo4j_schema.py - 创建 Neo4j schema

初始化知识图谱数据库 schema，包括：
- 节点标签定义
- 唯一性约束（防止重复数据导入）

注意：性能索引延迟到数据导入后创建（见 design.md D4）

Usage:
    python create_neo4j_schema.py
    python create_neo4j_schema.py --dry-run  # 仅打印 Cypher 语句
    python create_neo4j_schema.py --uri bolt://localhost:7687 --user neo4j --password xxx
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ Schema 定义 ============

# 节点标签（按 design.md D1）
NODE_LABELS = [
    'Subject',      # 学科
    'Stage',        # 学段（小学/初中/高中）
    'Grade',        # 年级
    'Textbook',     # 教材
    'Chapter',      # 章节
    'KnowledgePoint'  # 知识点
]

# 唯一性约束（按 design.md D5）
# 注意：仅创建约束，不创建性能索引
UNIQUE_CONSTRAINTS = [
    # (约束名, 标签, 属性)
    ('kp_uri_unique', 'KnowledgePoint', 'uri'),
    ('subject_code_unique', 'Subject', 'code'),
    ('textbook_isbn_unique', 'Textbook', 'isbn'),
]

# 关系类型（按 design.md D3）
# 注意：Neo4j 中关系类型在使用时自动创建，无需预定义
# 这里仅作为文档参考
RELATIONSHIP_TYPES = [
    # 层级关系
    'HAS_STAGE',
    'HAS_GRADE',
    'USE_TEXTBOOK',
    'HAS_CHAPTER',
    'HAS_KNOWLEDGE_POINT',
    # 学习依赖
    'PREREQUISITE',
    'TEACHES_BEFORE',
    'PREREQUISITE_ON',
    'PREREQUISITE_CANDIDATE',
    # 知识关联
    'RELATED_TO',
    'SUB_CATEGORY',
]


class Neo4jSchemaCreator:
    """Neo4j Schema 创建器"""

    def __init__(self, uri: str, user: str, password: str, database: str = 'neo4j'):
        """
        初始化 Neo4j 连接。

        Args:
            uri: Neo4j 连接 URI
            user: 用户名
            password: 密码
            database: 数据库名
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        """关闭连接"""
        self.driver.close()

    def test_connection(self) -> bool:
        """测试连接"""
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 1")
                result.single()
            logger.info("✓ Neo4j connection successful")
            return True
        except Exception as e:
            logger.error(f"✗ Neo4j connection failed: {e}")
            return False

    def create_constraints(self, dry_run: bool = False) -> int:
        """
        创建唯一性约束。

        Args:
            dry_run: 如果为 True，仅打印 Cypher 语句

        Returns:
            创建的约束数量
        """
        count = 0
        for constraint_name, label, property_name in UNIQUE_CONSTRAINTS:
            cypher = (
                f"CREATE CONSTRAINT IF NOT EXISTS {constraint_name} "
                f"FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE"
            )

            if dry_run:
                logger.info(f"[DRY-RUN] {cypher}")
            else:
                try:
                    with self.driver.session(database=self.database) as session:
                        session.run(cypher)
                    logger.info(f"✓ Created constraint: {constraint_name}")
                except Exception as e:
                    logger.error(f"✗ Failed to create constraint {constraint_name}: {e}")
                    continue

            count += 1

        return count

    def show_schema_info(self):
        """显示当前 schema 信息"""
        with self.driver.session(database=self.database) as session:
            # 显示约束
            result = session.run("SHOW CONSTRAINTS")
            constraints = list(result)
            logger.info(f"\n=== Current Constraints ({len(constraints)}) ===")
            for c in constraints:
                logger.info(f"  - {c['name']}: {c['labelsOrTypes']}({c['properties']})")

            # 显示索引（约束会自动创建 backing index）
            result = session.run("SHOW INDEXES WHERE type = 'RANGE'")
            indexes = list(result)
            logger.info(f"\n=== Current Indexes ({len(indexes)}) ===")
            for idx in indexes:
                logger.info(f"  - {idx['name']}: {idx['labelsOrTypes']}({idx['properties']})")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='创建 Neo4j schema（仅唯一性约束）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅打印 Cypher 语句，不执行'
    )
    parser.add_argument(
        '--uri',
        type=str,
        default=None,
        help='Neo4j URI (默认从环境变量 NEO4J_URI 读取)'
    )
    parser.add_argument(
        '--user',
        type=str,
        default=None,
        help='Neo4j 用户名 (默认从环境变量 NEO4J_USER 读取)'
    )
    parser.add_argument(
        '--password',
        type=str,
        default=None,
        help='Neo4j 密码 (默认从环境变量 NEO4J_PASSWORD 读取)'
    )
    parser.add_argument(
        '--database',
        type=str,
        default='neo4j',
        help='Neo4j 数据库名'
    )

    args = parser.parse_args()

    # Dry-run 模式
    if args.dry_run:
        print("\n=== DRY-RUN: Cypher Statements ===\n")
        for constraint_name, label, property_name in UNIQUE_CONSTRAINTS:
            print(f"CREATE CONSTRAINT IF NOT EXISTS {constraint_name} "
                  f"FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE;")
        print("\nNote: Performance indexes will be created after data import (see design.md D4)")
        sys.exit(0)

    # 从环境变量或参数获取连接信息
    import os
    uri = args.uri or os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = args.user or os.environ.get('NEO4J_USER', 'neo4j')
    password = args.password or os.environ.get('NEO4J_PASSWORD', '')

    # 创建 schema
    creator = Neo4jSchemaCreator(uri, user, password, args.database)

    try:
        # 测试连接
        if not creator.test_connection():
            sys.exit(1)

        # 创建约束
        logger.info("\n=== Creating Constraints ===")
        constraint_count = creator.create_constraints()

        # 显示 schema 信息
        creator.show_schema_info()

        print(f"\n✓ Schema initialization completed: {constraint_count} constraints created")
        print("Note: Performance indexes will be created after data import (see kg-math-knowledge-points)")

    except Exception as e:
        logger.error(f"Schema creation failed: {e}")
        sys.exit(1)
    finally:
        creator.close()


if __name__ == '__main__':
    main()