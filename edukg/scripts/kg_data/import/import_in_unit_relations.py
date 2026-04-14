#!/usr/bin/env python3
"""
导入知识点归属关系 (IN_UNIT) 到 Neo4j

功能：
1. 创建 IN_UNIT 关系（TextbookKP → Section/Chapter）
2. 知识点所属教学单元关联

数据来源：
    edukg/data/edukg/math/5_教材目录(Textbook)/output/in_unit_relations.json

使用方法：
    python import_in_unit_relations.py
    python import_in_unit_relations.py --dry-run
    python import_in_unit_relations.py --clear
    python import_in_unit_relations.py --stats
    python import_in_unit_relations.py --file PATH
"""
import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KG_DATA_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(KG_DATA_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

os.chdir(AI_SERVICE_DIR)

from edukg.core.neo4j.client import Neo4jClient
from edukg.config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(
    PROJECT_ROOT,
    "edukg", "data", "edukg", "math",
    "5_教材目录(Textbook)", "output", "in_unit_relations.json"
)


class InUnitRelationImporter:
    """IN_UNIT 关系导入器"""

    def __init__(self):
        self.client = Neo4jClient()
        logger.info(f"已连接 Neo4j: {settings.NEO4J_URI}")

    def close(self):
        self.client.close()

    def test_connection(self) -> bool:
        if self.client.health_check():
            version = self.client.get_version()
            logger.info(f"Neo4j 连接成功，版本: {version}")
            return True
        return False

    def load_data(self, file_path: str = None) -> List[Dict]:
        path = file_path or DATA_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(f"数据文件不存在: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"加载数据: {len(data)} 个归属关系")
        return data

    def clear_relations(self):
        logger.warning("清除已有的 IN_UNIT 关系...")
        with self.client.session() as session:
            result = session.run("MATCH ()-[r:IN_UNIT]->() DELETE r RETURN count(r) AS deleted")
            deleted = result.single()["deleted"]
            logger.info(f"已删除 {deleted} 个 IN_UNIT 关系")

    def import_in_unit_relations(self, relations: List[Dict], dry_run: bool = False) -> int:
        """
        创建 IN_UNIT 关系（TextbookKP → Section）

        注意：in_unit_relations.json 中 kp_uri 指向 TextbookKP，
        section_id 指向 Section 或 Chapter
        """
        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(relations)} 个 IN_UNIT 关系 ===\n")
            for rel in relations[:3]:
                print(f"MATCH (kp:TextbookKP {{uri: '{rel['kp_uri']}'}}) MATCH (s {{id: '{rel['section_id']}'}}) MERGE (kp)-[:IN_UNIT]->(s);")
            return len(relations)

        logger.info(f"\n=== 创建 {len(relations)} 个 IN_UNIT 关系 ===")

        # 先尝试匹配 Section，如果不存在则匹配 Chapter
        cypher = """
        UNWIND $relations AS rel
        MATCH (kp:TextbookKP {uri: rel.kp_uri})
        OPTIONAL MATCH (sec:Section {id: rel.section_id})
        OPTIONAL MATCH (chap:Chapter {id: rel.section_id})
        WITH kp, rel, sec, chap
        WHERE sec IS NOT NULL OR chap IS NOT NULL
        FOREACH (_ IN CASE WHEN sec IS NOT NULL THEN [1] ELSE [] END |
            MERGE (kp)-[:IN_UNIT]->(sec)
        )
        FOREACH (_ IN CASE WHEN chap IS NOT NULL AND sec IS NULL THEN [1] ELSE [] END |
            MERGE (kp)-[:IN_UNIT]->(chap)
        )
        """

        with self.client.session() as session:
            session.run(cypher, relations=relations)

        with self.client.session() as session:
            result = session.run("MATCH ()-[r:IN_UNIT]->() RETURN count(r) AS count")
            count = result.single()["count"]

        logger.info(f"✓ 已创建 {count} 个 IN_UNIT 关系")
        return count

    def show_statistics(self):
        with self.client.session() as session:
            result = session.run("MATCH ()-[r:IN_UNIT]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]

            # 关联到 Section 的数量
            result = session.run("MATCH ()-[:IN_UNIT]->(s:Section) RETURN count(s) AS count")
            to_section = result.single()["count"]

            # 关联到 Chapter 的数量
            result = session.run("MATCH ()-[:IN_UNIT]->(c:Chapter) RETURN count(c) AS count")
            to_chapter = result.single()["count"]

            # 没有归属的知识点数量
            result = session.run("MATCH (k:TextbookKP) WHERE NOT (k)-[:IN_UNIT]->() RETURN count(k) AS count")
            unlinked = result.single()["count"]

        logger.info("\n=== IN_UNIT 关系导入统计 ===")
        logger.info(f"  IN_UNIT 关系数: {rel_count}")
        logger.info(f"  关联到 Section: {to_section}")
        logger.info(f"  关联到 Chapter: {to_chapter}")
        logger.info(f"  未关联知识点: {unlinked}")

    def show_samples(self, limit: int = 10):
        logger.info(f"\n=== IN_UNIT 关系示例（前 {limit} 个） ===")
        with self.client.session() as session:
            result = session.run("""
                MATCH (kp:TextbookKP)-[:IN_UNIT]->(u)
                RETURN kp.label AS kp, labels(u)[0] AS unit_type, u.label AS unit
                ORDER BY kp.label
                LIMIT $limit
            """, limit=limit)
            for row in result:
                logger.info(f"  {row['kp']} → IN_UNIT → [{row['unit_type']}] {row['unit']}")


def main():
    parser = argparse.ArgumentParser(description='导入知识点归属关系到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅打印 Cypher 语句，不执行')
    parser.add_argument('--clear', action='store_true', help='导入前清除已有的 IN_UNIT 关系')
    parser.add_argument('--clear-only', action='store_true', help='仅清除已有的 IN_UNIT 关系，不导入')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')

    args = parser.parse_args()
    data_file = args.file if args.file else DATA_FILE

    importer = InUnitRelationImporter()

    try:
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        if args.clear_only:
            importer.clear_relations()
            importer.show_statistics()
            return

        if args.stats:
            importer.show_statistics()
            return

        relations = importer.load_data(data_file)

        if args.dry_run:
            importer.import_in_unit_relations(relations, dry_run=True)
            return

        if args.clear:
            importer.clear_relations()

        importer.import_in_unit_relations(relations)
        importer.show_statistics()
        importer.show_samples()

        logger.info("\n✅ IN_UNIT 关系导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
