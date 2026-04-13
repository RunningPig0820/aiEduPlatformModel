#!/usr/bin/env python3
"""
导入数学知识点到 Neo4j

功能：
1. 导入知识点 (Concept) 节点
2. 创建与概念类的 HAS_TYPE 关系
3. 支持重复导入（使用 MERGE）

使用方法：
    python import_math_concepts.py
    python import_math_concepts.py --file <数据文件>
    python import_math_concepts.py --stats
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

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
    "2_知识点实体(complete)", "math_concepts.json"
)


class MathConceptImporter:
    """数学知识点导入器"""

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

    def load_data(self) -> List[Dict]:
        """加载知识点数据"""
        if not os.path.exists(DATA_FILE):
            raise FileNotFoundError(f"数据文件不存在: {DATA_FILE}")

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            concepts = json.load(f)

        logger.info(f"加载数据: {len(concepts)} 个知识点")
        return concepts

    def create_constraints(self):
        """创建唯一性约束（防止重复）"""
        constraints = [
            # Concept URI 唯一
            """
            CREATE CONSTRAINT concept_uri_unique IF NOT EXISTS
            FOR (c:Concept) REQUIRE c.uri IS UNIQUE
            """,
        ]

        for cypher in constraints:
            try:
                with self.client.session() as session:
                    session.run(cypher)
                logger.info("✓ Concept 约束创建成功")
            except Exception as e:
                logger.warning(f"约束创建警告: {e}")

    def get_class_id_map(self) -> Dict[str, str]:
        """获取 Class 的 id 映射（用于建立关系）"""
        with self.client.session() as session:
            result = session.run("""
                MATCH (c:Class)
                RETURN c.id AS id, c.uri AS uri, c.label AS label
            """)
            class_map = {}
            for row in result:
                # 映射: type_id -> class_id
                class_id = row['id']
                # type_id 通常是 class_id 的前缀部分
                class_map[class_id] = class_id
            return class_map

    def import_concepts(self, concepts: List[Dict], batch_size: int = 500) -> int:
        """
        导入知识点节点（使用 MERGE 避免重复）

        Args:
            concepts: 知识点列表
            batch_size: 批量大小

        Returns:
            导入/更新的知识点数量
        """
        logger.info(f"\n=== 导入 {len(concepts)} 个知识点 ===")

        # 批量导入知识点节点
        imported = 0
        with self.client.session() as session:
            for i in range(0, len(concepts), batch_size):
                batch = concepts[i:i + batch_size]

                # 使用 MERGE 避免重复，创建 Concept 节点
                cypher = """
                UNWIND $concepts AS c
                MERGE (concept:Concept {uri: c.uri})
                SET concept.label = c.label,
                    concept.subject = 'math'
                """

                session.run(cypher, concepts=batch)
                imported += len(batch)

                if (i // batch_size + 1) % 10 == 0:
                    logger.info(f"  已处理 {imported}/{len(concepts)} 个知识点...")

        logger.info(f"✓ 知识点导入完成: {imported} 个")
        return imported

    def import_type_relations(self, concepts: List[Dict], batch_size: int = 500) -> int:
        """
        导入知识点与概念类的类型关系

        Args:
            concepts: 知识点列表（包含 types 字段）

        Returns:
            创建的关系数量
        """
        logger.info(f"\n=== 创建类型关系 ===")

        # 收集所有类型关系
        relations = []
        for c in concepts:
            for type_id in c.get('types', []):
                relations.append({
                    'concept_uri': c['uri'],
                    'class_id': type_id
                })

        if not relations:
            logger.info("没有类型关系需要创建")
            return 0

        logger.info(f"共 {len(relations)} 个类型关系待创建")

        # 批量创建关系（使用 MERGE 避免重复）
        created = 0
        with self.client.session() as session:
            for i in range(0, len(relations), batch_size):
                batch = relations[i:i + batch_size]

                # MATCH 知识点，OPTIONAL MATCH 概念类（可能不存在）
                cypher = """
                UNWIND $relations AS rel
                MATCH (c:Concept {uri: rel.concept_uri})
                OPTIONAL MATCH (cl:Class {id: rel.class_id})
                WITH c, cl, rel
                WHERE cl IS NOT NULL
                MERGE (c)-[:HAS_TYPE]->(cl)
                """

                session.run(cypher, relations=batch)
                created += len(batch)

        # 统计实际创建的关系数
        with self.client.session() as session:
            result = session.run("MATCH ()-[r:HAS_TYPE]->() RETURN count(r) AS count")
            actual_count = result.single()["count"]

        logger.info(f"✓ 类型关系创建完成: {actual_count} 个")
        return actual_count

    def show_statistics(self):
        """显示导入统计"""
        with self.client.session() as session:
            # 实体数量
            result = session.run("MATCH (c:Concept) RETURN count(c) AS count")
            entity_count = result.single()["count"]

            # 关系数量
            result = session.run("MATCH ()-[r:HAS_TYPE]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]

            # 按类型统计实体
            result = session.run("""
                MATCH (c:Concept)-[:HAS_TYPE]->(cl:Class)
                RETURN cl.label AS type, count(c) AS count
                ORDER BY count DESC
                LIMIT 15
            """)
            type_stats = list(result)

            # 没有类型的实体
            result = session.run("""
                MATCH (c:Concept)
                WHERE NOT (c)-[:HAS_TYPE]->()
                RETURN count(c) AS count
            """)
            no_type_count = result.single()["count"]

        logger.info("\n=== 导入统计 ===")
        logger.info(f"  Concept 节点数: {entity_count}")
        logger.info(f"  HAS_TYPE 关系数: {rel_count}")
        logger.info(f"  无类型的实体: {no_type_count}")

        logger.info("\n  按类型分布:")
        for row in type_stats:
            logger.info(f"    {row['type']}: {row['count']} 个")

    def show_sample(self, limit: int = 10):
        """显示示例数据"""
        logger.info(f"\n=== 示例数据 (前{limit}个) ===")

        with self.client.session() as session:
            result = session.run("""
                MATCH (c:Concept)-[:HAS_TYPE]->(cl:Class)
                RETURN c.label AS entity, cl.label AS type
                LIMIT $limit
            """, limit=limit)

            for i, row in enumerate(result, 1):
                logger.info(f"  {i}. {row['entity']} → 类型: {row['type']}")


def main():
    parser = argparse.ArgumentParser(description='导入数学知识点到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径（默认使用 math_concepts.json）')
    parser.add_argument('--dry-run', action='store_true', help='仅打印信息，不执行导入')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')
    parser.add_argument('--batch-size', type=int, default=500, help='批量导入大小')

    args = parser.parse_args()

    # 确定数据文件路径
    if args.file:
        data_file = args.file if os.path.isabs(args.file) else os.path.join(PROJECT_ROOT, args.file)
    else:
        data_file = DATA_FILE

    importer = MathConceptImporter()

    try:
        # 测试连接
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        # 仅显示统计
        if args.stats:
            importer.show_statistics()
            return

        # 加载数据
        if not os.path.exists(data_file):
            raise FileNotFoundError(f"数据文件不存在: {data_file}")

        with open(data_file, 'r', encoding='utf-8') as f:
            concepts = json.load(f)

        logger.info(f"加载数据文件: {data_file}")
        logger.info(f"知识点数量: {len(concepts)}")

        # Dry-run 模式
        if args.dry_run:
            logger.info(f"[DRY-RUN] 将导入 {len(concepts)} 个知识点")
            return

        # 创建约束
        importer.create_constraints()

        # 导入知识点
        importer.import_concepts(concepts, args.batch_size)

        # 导入类型关系
        importer.import_type_relations(concepts, args.batch_size)

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