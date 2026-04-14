#!/usr/bin/env python3
"""
导入章节节点 (Chapter) 及 CONTAINS 关系 (Textbook→Chapter) 到 Neo4j

功能：
1. 导入章节节点（135 个）
2. 创建 CONTAINS 关系（Textbook → Chapter）
3. 创建唯一性约束（uri, id）

数据来源：
    edukg/data/edukg/math/5_教材目录(Textbook)/output/chapters_enhanced.json

使用方法：
    python import_chapters.py
    python import_chapters.py --dry-run
    python import_chapters.py --clear
    python import_chapters.py --stats
    python import_chapters.py --file PATH
"""
import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any

# 添加项目根目录到 sys.path
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
    "5_教材目录(Textbook)", "output", "chapters_enhanced.json"
)


class ChapterImporter:
    """章节节点导入器"""

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
        logger.info(f"加载数据: {len(data)} 个章节")
        return data

    def create_constraints(self, dry_run: bool = False):
        constraints = [
            """
            CREATE CONSTRAINT chapter_uri_unique IF NOT EXISTS
            FOR (c:Chapter) REQUIRE c.uri IS UNIQUE
            """,
            """
            CREATE CONSTRAINT chapter_id_unique IF NOT EXISTS
            FOR (c:Chapter) REQUIRE c.id IS UNIQUE
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

    def clear_chapters(self):
        logger.warning("清除已有的 Chapter 节点及相关关系...")
        with self.client.session() as session:
            # 删除 Textbook→Chapter 的 CONTAINS 关系
            session.run("MATCH ()-[r:CONTAINS]->(c:Chapter) DELETE r")
            # 删除 Chapter→Section 的 CONTAINS 关系
            session.run("MATCH (c:Chapter)-[r:CONTAINS]->() DELETE r")
            result = session.run("MATCH (c:Chapter) DELETE c RETURN count(c) AS deleted")
            deleted = result.single()["deleted"]
            logger.info(f"已删除 {deleted} 个 Chapter 节点")

    def import_chapters(self, chapters: List[Dict], dry_run: bool = False) -> int:
        """导入章节节点"""
        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(chapters)} 个 Chapter 节点 ===\n")
            for ch in chapters[:3]:
                print(f"MERGE (c:Chapter {{uri: '{ch['uri']}'}}) SET c.id='{ch['id']}', c.label='{ch['label']}', c.order={ch.get('order', 0)};")
            return len(chapters)

        logger.info(f"\n=== 导入 {len(chapters)} 个章节节点 ===")

        cypher = """
        UNWIND $chapters AS ch
        MERGE (c:Chapter {uri: ch.uri})
        SET c.id = ch.id,
            c.label = ch.label,
            c.order = ch.order,
            c.textbook_id = ch.textbook_id,
            c.topic = ch.topic
        """

        with self.client.session() as session:
            session.run(cypher, chapters=chapters)

        logger.info(f"✓ 已导入 {len(chapters)} 个章节节点")
        return len(chapters)

    def import_contains_textbook_chapter(self, chapters: List[Dict], dry_run: bool = False) -> int:
        """创建 Textbook → Chapter 的 CONTAINS 关系"""
        relations = []
        for ch in chapters:
            relations.append({
                'textbook_id': ch['textbook_id'],
                'chapter_id': ch['id'],
            })

        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(relations)} 个 CONTAINS (Textbook→Chapter) 关系 ===\n")
            for rel in relations[:3]:
                print(f"MATCH (t:Textbook {{id: '{rel['textbook_id']}'}}) MATCH (c:Chapter {{id: '{rel['chapter_id']}'}}) MERGE (t)-[:CONTAINS]->(c);")
            return len(relations)

        logger.info(f"\n=== 创建 {len(relations)} 个 CONTAINS (Textbook→Chapter) 关系 ===")

        cypher = """
        UNWIND $relations AS rel
        MATCH (t:Textbook {id: rel.textbook_id})
        MATCH (c:Chapter {id: rel.chapter_id})
        MERGE (t)-[:CONTAINS]->(c)
        """

        with self.client.session() as session:
            session.run(cypher, relations=relations)

        with self.client.session() as session:
            result = session.run("MATCH ()-[r:CONTAINS]->(c:Chapter) RETURN count(r) AS count")
            count = result.single()["count"]

        logger.info(f"✓ 已创建 {count} 个 CONTAINS (Textbook→Chapter) 关系")
        return count

    def show_statistics(self):
        with self.client.session() as session:
            result = session.run("MATCH (c:Chapter) RETURN count(c) AS count")
            node_count = result.single()["count"]

            result = session.run("MATCH ()-[r:CONTAINS]->(c:Chapter) RETURN count(r) AS count")
            rel_count = result.single()["count"]

            result = session.run("""
                MATCH (t:Textbook)-[:CONTAINS]->(c:Chapter)
                RETURN t.label AS textbook, count(c) AS chapters
                ORDER BY textbook
            """)
            by_textbook = {r["textbook"]: r["chapters"] for r in result}

        logger.info("\n=== 章节导入统计 ===")
        logger.info(f"  Chapter 节点数: {node_count}")
        logger.info(f"  CONTAINS (Textbook→Chapter) 关系数: {rel_count}")
        if by_textbook:
            logger.info(f"  按教材分布: {by_textbook}")

    def show_samples(self, limit: int = 10):
        logger.info(f"\n=== 章节示例（前 {limit} 个） ===")
        with self.client.session() as session:
            result = session.run("""
                MATCH (t:Textbook)-[:CONTAINS]->(c:Chapter)
                RETURN t.label AS textbook, c.label AS chapter, c.order AS `order`
                ORDER BY t.label, c.order
                LIMIT $limit
            """, limit=limit)
            for row in result:
                logger.info(f"  {row['textbook']} → {row['chapter']} (order={row['order']})")


def main():
    parser = argparse.ArgumentParser(description='导入章节节点到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅打印 Cypher 语句，不执行')
    parser.add_argument('--clear', action='store_true', help='导入前清除已有的 Chapter 节点')
    parser.add_argument('--clear-only', action='store_true', help='仅清除已有的 Chapter 节点，不导入')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')

    args = parser.parse_args()
    data_file = args.file if args.file else DATA_FILE

    importer = ChapterImporter()

    try:
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        if args.clear_only:
            importer.clear_chapters()
            importer.show_statistics()
            return

        if args.stats:
            importer.show_statistics()
            return

        chapters = importer.load_data(data_file)

        if args.dry_run:
            importer.create_constraints(dry_run=True)
            importer.import_chapters(chapters, dry_run=True)
            importer.import_contains_textbook_chapter(chapters, dry_run=True)
            return

        importer.create_constraints()

        if args.clear:
            importer.clear_chapters()

        importer.import_chapters(chapters)
        importer.import_contains_textbook_chapter(chapters)
        importer.show_statistics()
        importer.show_samples()

        logger.info("\n✅ 章节导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
