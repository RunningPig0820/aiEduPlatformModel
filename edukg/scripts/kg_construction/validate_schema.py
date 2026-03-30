#!/usr/bin/env python
"""
validate_schema.py - 验证 Neo4j schema 是否正确创建

检查：
- 节点标签是否存在
- 唯一性约束是否生效

注意：不验证性能索引（索引延迟到数据导入后创建）

Usage:
    python validate_schema.py
    python validate_schema.py --verbose
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

# 预期的节点标签
EXPECTED_LABELS = [
    'Subject',
    'Stage',
    'Grade',
    'Textbook',
    'Chapter',
    'KnowledgePoint'
]

# 预期的约束（按 design.md D5）
EXPECTED_CONSTRAINTS = [
    ('kp_uri_unique', 'KnowledgePoint', 'uri'),
    ('subject_code_unique', 'Subject', 'code'),
    ('textbook_isbn_unique', 'Textbook', 'isbn'),
]


class SchemaValidator:
    """Schema 验证器"""

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

    def get_existing_labels(self) -> set:
        """获取数据库中已有的节点标签"""
        with self.driver.session(database=self.database) as session:
            result = session.run("CALL db.labels()")
            return {record['label'] for record in result}

    def get_existing_constraints(self) -> list:
        """获取数据库中已有的约束"""
        with self.driver.session(database=self.database) as session:
            result = session.run("SHOW CONSTRAINTS")
            return list(result)

    def validate(self, verbose: bool = False) -> tuple[bool, dict]:
        """
        验证 schema 是否正确。

        Args:
            verbose: 是否显示详细信息

        Returns:
            (是否通过, 详细报告)
        """
        report = {
            'labels': {'expected': len(EXPECTED_LABELS), 'found': 0, 'missing': []},
            'constraints': {'expected': len(EXPECTED_CONSTRAINTS), 'found': 0, 'missing': []},
        }

        all_passed = True

        # 验证标签
        existing_labels = self.get_existing_labels()
        missing_labels = []
        for label in EXPECTED_LABELS:
            if label not in existing_labels:
                missing_labels.append(label)

        report['labels']['found'] = len(EXPECTED_LABELS) - len(missing_labels)
        report['labels']['missing'] = missing_labels

        if missing_labels:
            all_passed = False
            if verbose:
                logger.warning(f"Missing labels: {missing_labels}")

        # 验证约束
        existing_constraints = self.get_existing_constraints()
        existing_constraint_names = {c['name'] for c in existing_constraints}
        missing_constraints = []

        for constraint_name, label, prop in EXPECTED_CONSTRAINTS:
            if constraint_name not in existing_constraint_names:
                missing_constraints.append(constraint_name)

        report['constraints']['found'] = len(EXPECTED_CONSTRAINTS) - len(missing_constraints)
        report['constraints']['missing'] = missing_constraints

        if missing_constraints:
            all_passed = False
            if verbose:
                logger.warning(f"Missing constraints: {missing_constraints}")

        return all_passed, report


def print_report(report: dict, verbose: bool = False):
    """打印验证报告"""
    print("\nVALIDATION REPORT")
    print("==================")

    # 标签
    labels = report['labels']
    if labels['missing']:
        print(f"Labels: {labels['found']}/{labels['expected']} ✗ (Missing: {', '.join(labels['missing'])})")
    else:
        print(f"Labels: {labels['found']}/{labels['expected']} ✓")

    # 约束
    constraints = report['constraints']
    if constraints['missing']:
        print(f"Constraints: {constraints['found']}/{constraints['expected']} ✗ (Missing: {', '.join(constraints['missing'])})")
    else:
        print(f"Constraints: {constraints['found']}/{constraints['expected']} ✓")

    print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='验证 Neo4j schema'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细信息'
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

    # 从环境变量或参数获取连接信息
    import os
    uri = args.uri or os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = args.user or os.environ.get('NEO4J_USER', 'neo4j')
    password = args.password or os.environ.get('NEO4J_PASSWORD', '')

    if not password:
        logger.error("Neo4j password not provided. Set NEO4J_PASSWORD environment variable or use --password")
        sys.exit(1)

    # 验证
    validator = SchemaValidator(uri, user, password, args.database)

    try:
        passed, report = validator.validate(verbose=args.verbose)
        print_report(report, verbose=args.verbose)

        if passed:
            print("All schema elements are correctly created.")
            print("Exit code: 0")
            sys.exit(0)
        else:
            print("Missing schema elements detected. Please run create_neo4j_schema.py")
            print("Exit code: 1")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    finally:
        validator.close()


if __name__ == '__main__':
    main()