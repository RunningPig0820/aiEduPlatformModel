#!/usr/bin/env python3
"""
导入数学定义/定理到 Neo4j

功能：
1. 导入 Statement 节点
2. 创建 HAS_TYPE 关系 (Statement → Class)
3. 支持重复导入（使用 MERGE）

使用方法：
    python import_math_statements.py --file <数据文件>
    python import_math_statements.py --stats
"""
import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any

# 添加项目根目录到 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 添加 ai-edu-ai-service 目录到 sys.path
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

# 切换工作目录以加载 .env
os.chdir(AI_SERVICE_DIR)

from edukg.core.neo4j.client import Neo4jClient
from edukg.config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认数据文件
DATA_FILE = os.path.join(
    PROJECT_ROOT,
    "edukg", "data", "edukg", "math",
    "3_定义_定理(Statement)", "primary_math_statements.json"
)


class StatementImporter:
    """数学定义/定理导入器"""

    def __init__(self):
        self.client = Neo4jClient()
        logger.info(f"已连接 Neo4j: {settings.NEO4J_URI}")

    def close(self):
        self.client.close()

    def test_connection(self) -> bool:
        """测试连接"""
        if self.client.health_check():
            version = self.client.get_version()
            logger.info(f"Neo4j 连接成功，版本: {version}")
            return True
        return False

    def import_statements(self, statements: List[Dict], batch_size: int = 500) -> int:
        """
        导入 Statement 节点

        Args:
            statements: Statement 列表，每个包含 uri, label, types, content
            batch_size: 批量大小

        Returns:
            导入的节点数量
        """
        logger.info(f"\n=== 导入 {len(statements)} 个 Statement ===")

        with self.client.session() as session:
            for i in range(0, len(statements), batch_size):
                batch = statements[i:i + batch_size]

                # 准备数据，不导入 subject 属性
                batch_data = []
                for s in batch:
                    batch_data.append({
                        'uri': s['uri'],
                        'label': s['label'],
                        'content': s.get('content', '')
                    })

                cypher = """
                UNWIND $statements AS s
                MERGE (stmt:Statement {uri: s.uri})
                SET stmt.label = s.label, stmt.content = s.content
                """

                session.run(cypher, statements=batch_data)

        # 统计
        with self.client.session() as session:
            result = session.run("MATCH (s:Statement) RETURN count(s) AS count")
            count = result.single()["count"]

        logger.info(f"✓ Statement 节点导入完成: 当前共 {count} 个")
        return count

    def import_has_type_relations(self, statements: List[Dict], batch_size: int = 500) -> int:
        """
        导入 HAS_TYPE 关系 (Statement → Class)

        Args:
            statements: Statement 列表，每个包含 uri, types

        Returns:
            创建的关系数量
        """
        logger.info(f"\n=== 创建 HAS_TYPE 关系 ===")

        # 收集类型关系
        relations = []
        for s in statements:
            if not s.get('types'):
                continue
            for t in s['types']:
                type_uri = f"http://edukg.org/knowledge/0.1/class/math#{t}"
                relations.append({
                    'statement_uri': s['uri'],
                    'type_uri': type_uri
                })

        if not relations:
            logger.info("没有类型关系需要创建")
            return 0

        logger.info(f"共 {len(relations)} 个类型关系待创建")

        with self.client.session() as session:
            for i in range(0, len(relations), batch_size):
                batch = relations[i:i + batch_size]

                cypher = """
                UNWIND $relations AS rel
                MATCH (s:Statement {uri: rel.statement_uri})
                OPTIONAL MATCH (c:Class {uri: rel.type_uri})
                WITH s, c, rel
                WHERE c IS NOT NULL
                MERGE (s)-[:HAS_TYPE]->(c)
                """

                session.run(cypher, relations=batch)

        # 统计
        with self.client.session() as session:
            result = session.run("""
                MATCH (s:Statement)-[:HAS_TYPE]->(c:Class)
                WHERE s.uri CONTAINS '0.2'
                RETURN count(s) AS count
            """)
            count = result.single()["count"]

        logger.info(f"✓ HAS_TYPE 关系创建完成: {count} 个")
        return count

    def show_statistics(self):
        """显示统计信息"""
        with self.client.session() as session:
            # Statement 总数
            result = session.run("MATCH (s:Statement) RETURN count(s) AS count")
            total = result.single()["count"]

            # v0.2 版本
            result = session.run("""
                MATCH (s:Statement)
                WHERE s.uri CONTAINS '0.2'
                RETURN count(s) AS count
            """)
            v02_count = result.single()["count"]

            # 有 content 的
            result = session.run("""
                MATCH (s:Statement)
                WHERE s.content IS NOT NULL AND s.content <> ''
                RETURN count(s) AS count
            """)
            content_count = result.single()["count"]

        logger.info("\n=== 导入统计 ===")
        logger.info(f"  Statement 总数: {total}")
        logger.info(f"  小学新增 (v0.2): {v02_count}")
        logger.info(f"  有 content: {content_count}")

    def show_sample(self, limit: int = 5):
        """显示示例"""
        logger.info(f"\n=== 小学 Statement 示例 ===")

        with self.client.session() as session:
            result = session.run("""
                MATCH (s:Statement)
                WHERE s.uri CONTAINS '0.2'
                RETURN s.label AS label, s.content AS content
                LIMIT $limit
            """, limit=limit)

            for i, row in enumerate(result, 1):
                content = row['content'][:50] + '...' if len(row['content']) > 50 else row['content']
                logger.info(f"  {i}. {row['label']}: {content}")


def main():
    parser = argparse.ArgumentParser(description='导入数学定义/定理到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')
    parser.add_argument('--batch-size', type=int, default=500, help='批量导入大小')

    args = parser.parse_args()

    # 确定数据文件
    if args.file:
        data_file = args.file if os.path.isabs(args.file) else os.path.join(PROJECT_ROOT, args.file)
    else:
        data_file = DATA_FILE

    importer = StatementImporter()

    try:
        # 测试连接
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        # 仅显示统计
        if args.stats:
            importer.show_statistics()
            importer.show_sample()
            return

        # 加载数据
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"数据文件不存在: {data_file}")

        with open(data_file, 'r', encoding='utf-8') as f:
            statements = json.load(f)

        logger.info(f"加载数据文件: {data_file}")
        logger.info(f"Statement 数量: {len(statements)}")

        # 导入 Statement 节点
        importer.import_statements(statements, args.batch_size)

        # 导入 HAS_TYPE 关系
        importer.import_has_type_relations(statements, args.batch_size)

        # 显示统计
        importer.show_statistics()
        importer.show_sample()

        logger.info("\n✅ 导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()


if __name__ == '__main__':
    main()