#!/usr/bin/env python3
"""
导入教材知识点节点 (TextbookKP) 到 Neo4j

功能：
1. 导入教材知识点节点（1350 个）
2. 包含难度、重要性、认知水平、Topic 等属性
3. 创建唯一性约束（uri）

数据来源：
    edukg/data/edukg/math/5_教材目录(Textbook)/output/textbook_kps.json

使用方法：
    python import_textbook_kps.py
    python import_textbook_kps.py --dry-run
    python import_textbook_kps.py --clear
    python import_textbook_kps.py --stats
    python import_textbook_kps.py --file PATH
"""
import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any
from collections import Counter

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
    "5_教材目录(Textbook)", "output", "textbook_kps.json"
)


class TextbookKPImporter:
    """教材知识点节点导入器"""

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
        logger.info(f"加载数据: {len(data)} 个教材知识点")
        return data

    def create_constraints(self, dry_run: bool = False):
        constraints = [
            """
            CREATE CONSTRAINT textbookkp_uri_unique IF NOT EXISTS
            FOR (k:TextbookKP) REQUIRE k.uri IS UNIQUE
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

    def clear_kps(self):
        logger.warning("清除已有的 TextbookKP 节点及相关关系...")
        with self.client.session() as session:
            # 删除 IN_UNIT 关系
            session.run("MATCH (k:TextbookKP)-[r:IN_UNIT]->() DELETE r")
            # 删除 MATCHES_KG 关系
            session.run("MATCH (k:TextbookKP)-[r:MATCHES_KG]->() DELETE r")
            # 删除 PREREQUISITE 关系
            session.run("MATCH ()-[r:PREREQUISITE]->(k:TextbookKP) DELETE r")
            session.run("MATCH (k:TextbookKP)-[r:PREREQUISITE]->() DELETE r")
            result = session.run("MATCH (k:TextbookKP) DELETE k RETURN count(k) AS deleted")
            deleted = result.single()["deleted"]
            logger.info(f"已删除 {deleted} 个 TextbookKP 节点")

    def import_kps(self, kps: List[Dict], dry_run: bool = False) -> int:
        """导入教材知识点节点"""
        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(kps)} 个 TextbookKP 节点 ===\n")
            for kp in kps[:3]:
                print(f"MERGE (k:TextbookKP {{uri: '{kp['uri']}'}}) SET k.label='{kp['label']}', k.stage='{kp['stage']}', k.grade='{kp['grade']}';")
            return len(kps)

        logger.info(f"\n=== 导入 {len(kps)} 个教材知识点节点 ===")

        cypher = """
        UNWIND $kps AS kp
        MERGE (k:TextbookKP {uri: kp.uri})
        SET k.label = kp.label,
            k.stage = kp.stage,
            k.grade = kp.grade,
            k.section_id = kp.section_id,
            k.textbook_id = kp.textbook_id,
            k.difficulty = kp.difficulty,
            k.difficulty_source = kp.difficulty_source,
            k.importance = kp.importance,
            k.importance_source = kp.importance_source,
            k.cognitive_level = kp.cognitive_level,
            k.cognitive_level_source = kp.cognitive_level_source,
            k.topic = kp.topic,
            k.topic_source = kp.topic_source
        """

        with self.client.session() as session:
            session.run(cypher, kps=kps)

        logger.info(f"✓ 已导入 {len(kps)} 个教材知识点节点")
        return len(kps)

    def show_statistics(self):
        with self.client.session() as session:
            result = session.run("MATCH (k:TextbookKP) RETURN count(k) AS count")
            node_count = result.single()["count"]

            # 按学段分布
            result = session.run("MATCH (k:TextbookKP) RETURN k.stage AS stage, count(k) AS cnt ORDER BY cnt DESC")
            by_stage = {r["stage"]: r["cnt"] for r in result}

            # 按年级分布
            result = session.run("MATCH (k:TextbookKP) RETURN k.grade AS grade, count(k) AS cnt ORDER BY grade")
            by_grade = {r["grade"]: r["cnt"] for r in result}

            # 按 Topic 分布
            result = session.run("MATCH (k:TextbookKP) RETURN k.topic AS topic, count(k) AS cnt ORDER BY cnt DESC")
            by_topic = {r["topic"]: r["cnt"] for r in result}

            # 按难度分布
            result = session.run("MATCH (k:TextbookKP) RETURN k.difficulty AS diff, count(k) AS cnt ORDER BY diff")
            by_diff = {r["diff"]: r["cnt"] for r in result}

            # 按认知水平分布
            result = session.run("MATCH (k:TextbookKP) RETURN k.cognitive_level AS level, count(k) AS cnt ORDER BY cnt DESC")
            by_cognitive = {r["level"]: r["cnt"] for r in result}

        logger.info("\n=== 教材知识点导入统计 ===")
        logger.info(f"  TextbookKP 节点数: {node_count}")
        logger.info(f"  按学段分布: {by_stage}")
        logger.info(f"  按年级分布: {by_grade}")
        logger.info(f"  按 Topic 分布: {by_topic}")
        logger.info(f"  按难度分布: {by_diff}")
        logger.info(f"  按认知水平分布: {by_cognitive}")

    def show_samples(self, limit: int = 10):
        logger.info(f"\n=== 知识点示例（前 {limit} 个） ===")
        with self.client.session() as session:
            result = session.run("""
                MATCH (k:TextbookKP)
                RETURN k.label AS label, k.stage AS stage, k.grade AS grade,
                       k.difficulty AS diff, k.importance AS imp, k.cognitive_level AS level, k.topic AS topic
                ORDER BY k.grade, k.label
                LIMIT $limit
            """, limit=limit)
            for row in result:
                logger.info(f"  {row['label']} ({row['stage']}/{row['grade']}) diff={row['diff']}, imp={row['imp']}, level={row['level']}, topic={row['topic']}")


def main():
    parser = argparse.ArgumentParser(description='导入教材知识点节点到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅打印 Cypher 语句，不执行')
    parser.add_argument('--clear', action='store_true', help='导入前清除已有的 TextbookKP 节点')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')

    args = parser.parse_args()
    data_file = args.file if args.file else DATA_FILE

    importer = TextbookKPImporter()

    try:
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        if args.stats:
            importer.show_statistics()
            return

        kps = importer.load_data(data_file)

        if args.dry_run:
            importer.create_constraints(dry_run=True)
            importer.import_kps(kps, dry_run=True)
            return

        importer.create_constraints()

        if args.clear:
            importer.clear_kps()

        importer.import_kps(kps)
        importer.show_statistics()
        importer.show_samples()

        logger.info("\n✅ 教材知识点导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
