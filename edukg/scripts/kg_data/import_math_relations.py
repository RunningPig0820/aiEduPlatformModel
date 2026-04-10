#!/usr/bin/env python3
"""
导入数学知识点关联关系到 Neo4j

功能：
1. 导入 9,873 个 RELATED_TO 关系
2. 只匹配已存在的实体（不会创建新节点）
3. 支持重复导入（使用 MERGE）

使用方法：
    python import_math_relations.py
    python import_math_relations.py --dry-run
    python import_math_relations.py --stats
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
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

# 数据文件路径
DATA_FILE = os.path.join(
    PROJECT_ROOT,
    "edukg", "data", "edukg", "math",
    "4_知识点关联关系(Relation)", "math_knowledge_relations.json"
)


class MathRelationImporter:
    """数学知识点关联关系导入器"""

    def __init__(self, data_file: str = None):
        self.client = Neo4jClient()
        self.data_file = data_file or DATA_FILE
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

    def load_data(self) -> List[Dict]:
        """加载关系数据"""
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"数据文件不存在: {self.data_file}")

        with open(self.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        relations = data.get('relations', [])
        logger.info(f"加载数据文件: {self.data_file}")
        logger.info(f"关系数量: {len(relations)}")
        return relations

    def import_relations(self, relations: List[Dict], batch_size: int = 1000) -> int:
        """
        导入 RELATED_TO 关系

        Args:
            relations: 关系列表
            batch_size: 批量大小

        Returns:
            创建的关系数量
        """
        logger.info(f"\n=== 导入 {len(relations)} 个 RELATED_TO 关系 ===")

        # 构建关系数据
        rel_data = []
        for r in relations:
            rel_data.append({
                'from_uri': r['from']['uri'],
                'to_uri': r['to']['uri'],
                'from_label': r['from'].get('label', ''),
                'to_label': r['to'].get('label', '')
            })

        # 批量导入
        imported = 0
        with self.client.session() as session:
            for i in range(0, len(rel_data), batch_size):
                batch = rel_data[i:i + batch_size]

                # 判断 from 的节点类型 (statement 或 instance)
                # Statement → Concept 的 RELATED_TO 关系
                cypher = """
                UNWIND $relations AS rel
                MATCH (from {uri: rel.from_uri})
                MATCH (to {uri: rel.to_uri})
                MERGE (from)-[r:RELATED_TO]->(to)
                """

                session.run(cypher, relations=batch)
                imported += len(batch)

                if (i // batch_size + 1) % 5 == 0:
                    logger.info(f"  已处理 {imported}/{len(relations)} 个关系...")

        # 统计实际创建的关系数
        with self.client.session() as session:
            result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count")
            actual_count = result.single()["count"]

        logger.info(f"✓ 关系导入完成: 实际创建 {actual_count} 个")
        return actual_count

    def show_statistics(self):
        """显示统计信息"""
        with self.client.session() as session:
            # 关系总数
            result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]

            # 出度最多的节点
            result = session.run("""
                MATCH (n)-[r:RELATED_TO]->()
                RETURN n.label AS label, labels(n)[0] AS type, count(r) AS out_count
                ORDER BY out_count DESC
                LIMIT 10
            """)
            top_out = list(result)

            # 入度最多的节点
            result = session.run("""
                MATCH ()-[r:RELATED_TO]->(n)
                RETURN n.label AS label, labels(n)[0] AS type, count(r) AS in_count
                ORDER BY in_count DESC
                LIMIT 10
            """)
            top_in = list(result)

            # 小学 Statement 的 RELATED_TO 统计
            result = session.run("""
                MATCH (s:Statement)-[r:RELATED_TO]->()
                WHERE s.uri CONTAINS '0.2'
                RETURN count(r) AS count
            """)
            v02_count = result.single()["count"]

        logger.info("\n=== 统计信息 ===")
        logger.info(f"  RELATED_TO 关系总数: {rel_count}")
        logger.info(f"  小学 Statement 关联数 (v0.2): {v02_count}")

        logger.info("\n  出度最多的节点（关联出去最多）:")
        for row in top_out:
            logger.info(f"    {row['label']} ({row['type']}): {row['out_count']}")

        logger.info("\n  入度最多的节点（被关联最多）:")
        for row in top_in:
            logger.info(f"    {row['label']} ({row['type']}): {row['in_count']}")

    def show_sample(self, limit: int = 10):
        """显示示例关系"""
        logger.info(f"\n=== 示例关系 (前{limit}个) ===")

        with self.client.session() as session:
            # 小学 Statement 的 RELATED_TO 示例
            result = session.run("""
                MATCH (from:Statement)-[r:RELATED_TO]->(to:Concept)
                WHERE from.uri CONTAINS '0.2'
                RETURN from.label AS from_label, to.label AS to_label
                LIMIT $limit
            """, limit=limit)

            count = 0
            for row in result:
                count += 1
                logger.info(f"  {count}. {row['from_label']} → RELATED_TO → {row['to_label']}")

            if count == 0:
                # 如果没有小学数据，显示一般示例
                result = session.run("""
                    MATCH (from)-[r:RELATED_TO]->(to)
                    RETURN from.label AS from_label, labels(from)[0] AS from_type,
                           to.label AS to_label, labels(to)[0] AS to_type
                    LIMIT $limit
                """, limit=limit)
                for row in result:
                    logger.info(f"  {row['from_label']} ({row['from_type']}) → {row['to_label']} ({row['to_type']})")


def main():
    parser = argparse.ArgumentParser(description='导入数学知识点关联关系到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅打印信息，不执行导入')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')
    parser.add_argument('--batch-size', type=int, default=500, help='批量导入大小')

    args = parser.parse_args()

    # 确定数据文件
    if args.file:
        data_file = args.file if os.path.isabs(args.file) else os.path.join(PROJECT_ROOT, args.file)
    else:
        data_file = DATA_FILE

    importer = MathRelationImporter(data_file)

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
        relations = importer.load_data()

        # Dry-run 模式
        if args.dry_run:
            logger.info(f"[DRY-RUN] 将导入 {len(relations)} 个 RELATED_TO 关系")
            importer.show_sample()
            return

        # 导入关系
        importer.import_relations(relations, args.batch_size)

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