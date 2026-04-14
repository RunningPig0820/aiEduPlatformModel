#!/usr/bin/env python3
"""
导入小节节点 (Section) 及 CONTAINS 关系 (Chapter→Section) 到 Neo4j

功能：
1. 导入小节节点（549 个）
2. 创建 CONTAINS 关系（Chapter → Section）
3. 创建唯一性约束（uri, id）

数据来源：
    edukg/data/edukg/math/5_教材目录(Textbook)/output/sections.json

使用方法：
    python import_sections.py
    python import_sections.py --dry-run
    python import_sections.py --clear
    python import_sections.py --stats
    python import_sections.py --file PATH
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
    "5_教材目录(Textbook)", "output", "sections.json"
)


class SectionImporter:
    """小节节点导入器"""

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
        logger.info(f"加载数据: {len(data)} 个小节")
        return data

    def create_constraints(self, dry_run: bool = False):
        constraints = [
            """
            CREATE CONSTRAINT section_uri_unique IF NOT EXISTS
            FOR (s:Section) REQUIRE s.uri IS UNIQUE
            """,
            """
            CREATE CONSTRAINT section_id_unique IF NOT EXISTS
            FOR (s:Section) REQUIRE s.id IS UNIQUE
            """,
        ]
        for cypher in constraints:
            if dry_run:
                logger.info(f"[DRY-RUN] {cypher.strip()}")
            else:
                try:
                    with self.client.session() as session:
                        session.run(cypher)
                    logger.info("✓ 约束创建成功")
                except Exception as e:
                    logger.warning(f"约束创建警告: {e}")

    def clear_sections(self):
        logger.warning("清除已有的 Section 节点及相关关系...")
        with self.client.session() as session:
            # 删除 Chapter→Section 的 CONTAINS 关系
            session.run("MATCH (c:Chapter)-[r:CONTAINS]->(s:Section) DELETE r")
            # 删除 TextbookKP→Section 的 IN_UNIT 关系
            session.run("MATCH ()-[r:IN_UNIT]->(s:Section) DELETE r")
            result = session.run("MATCH (s:Section) DELETE s RETURN count(s) AS deleted")
            deleted = result.single()["deleted"]
            logger.info(f"已删除 {deleted} 个 Section 节点")

    def import_sections(self, sections: List[Dict], dry_run: bool = False) -> int:
        """导入小节节点"""
        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(sections)} 个 Section 节点 ===\n")
            for sec in sections[:3]:
                print(f"MERGE (s:Section {{uri: '{sec['uri']}'}}) SET s.id='{sec['id']}', s.label='{sec['label']}', s.order={sec.get('order', 0)}, s.chapter_id='{sec.get('chapter_id', '')}';")
            return len(sections)

        logger.info(f"\n=== 导入 {len(sections)} 个小节节点 ===")

        cypher = """
        UNWIND $sections AS sec
        MERGE (s:Section {uri: sec.uri})
        SET s.id = sec.id,
            s.label = sec.label,
            s.order = sec.order,
            s.chapter_id = sec.chapter_id,
            s.mark = sec.mark
        """

        with self.client.session() as session:
            session.run(cypher, sections=sections)

        logger.info(f"✓ 已导入 {len(sections)} 个小节节点")
        return len(sections)

    def import_contains_chapter_section(self, sections: List[Dict], dry_run: bool = False) -> int:
        """创建 Chapter → Section 的 CONTAINS 关系"""
        relations = []
        for sec in sections:
            relations.append({
                'chapter_id': sec['chapter_id'],
                'section_id': sec['id'],
            })

        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(relations)} 个 CONTAINS (Chapter→Section) 关系 ===\n")
            for rel in relations[:3]:
                print(f"MATCH (c:Chapter {{id: '{rel['chapter_id']}'}}) MATCH (s:Section {{id: '{rel['section_id']}'}}) MERGE (c)-[:CONTAINS]->(s);")
            return len(relations)

        logger.info(f"\n=== 创建 {len(relations)} 个 CONTAINS (Chapter→Section) 关系 ===")

        cypher = """
        UNWIND $relations AS rel
        MATCH (c:Chapter {id: rel.chapter_id})
        MATCH (s:Section {id: rel.section_id})
        MERGE (c)-[:CONTAINS]->(s)
        """

        with self.client.session() as session:
            session.run(cypher, relations=relations)

        with self.client.session() as session:
            result = session.run("MATCH (c:Chapter)-[r:CONTAINS]->(s:Section) RETURN count(r) AS count")
            count = result.single()["count"]

        logger.info(f"✓ 已创建 {count} 个 CONTAINS (Chapter→Section) 关系")
        return count

    def show_statistics(self):
        with self.client.session() as session:
            result = session.run("MATCH (s:Section) RETURN count(s) AS count")
            node_count = result.single()["count"]

            result = session.run("MATCH (c:Chapter)-[r:CONTAINS]->(s:Section) RETURN count(r) AS count")
            rel_count = result.single()["count"]

        logger.info("\n=== 小节导入统计 ===")
        logger.info(f"  Section 节点数: {node_count}")
        logger.info(f"  CONTAINS (Chapter→Section) 关系数: {rel_count}")

    def show_samples(self, limit: int = 10):
        logger.info(f"\n=== 小节示例（前 {limit} 个） ===")
        with self.client.session() as session:
            result = session.run("""
                MATCH (c:Chapter)-[:CONTAINS]->(s:Section)
                RETURN c.label AS chapter, s.label AS section, s.order AS `order`, s.mark AS mark
                ORDER BY c.label, s.order
                LIMIT $limit
            """, limit=limit)
            for row in result:
                mark_str = f" [{row['mark']}]" if row['mark'] else ""
                logger.info(f"  {row['chapter']} → {row['section']}{mark_str} (order={row['order']})")


def main():
    parser = argparse.ArgumentParser(description='导入小节节点到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅打印 Cypher 语句，不执行')
    parser.add_argument('--clear', action='store_true', help='导入前清除已有的 Section 节点')
    parser.add_argument('--clear-only', action='store_true', help='仅清除已有的 Section 节点，不导入')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')

    args = parser.parse_args()
    data_file = args.file if args.file else DATA_FILE

    importer = SectionImporter()

    try:
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        if args.clear_only:
            importer.clear_sections()
            importer.show_statistics()
            return

        if args.stats:
            importer.show_statistics()
            return

        sections = importer.load_data(data_file)

        if args.dry_run:
            importer.create_constraints(dry_run=True)
            importer.import_sections(sections, dry_run=True)
            importer.import_contains_chapter_section(sections, dry_run=True)
            return

        importer.create_constraints()

        if args.clear:
            importer.clear_sections()

        importer.import_sections(sections)
        importer.import_contains_chapter_section(sections)
        importer.show_statistics()
        importer.show_samples()

        logger.info("\n✅ 小节导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
