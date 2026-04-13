#!/usr/bin/env python3
"""
导入知识点匹配关系 (MATCHES_KG) 到 Neo4j

功能：
1. 创建 MATCHES_KG 关系（TextbookKP → Concept）
2. 仅导入已匹配的记录（matched=true）
3. 包含 confidence 和 method 属性

数据来源：
    edukg/data/edukg/math/5_教材目录(Textbook)/output/matches_kg_relations.json

使用方法：
    python import_matches_kg.py
    python import_matches_kg.py --dry-run
    python import_matches_kg.py --clear
    python import_matches_kg.py --stats
    python import_matches_kg.py --file PATH
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
    "5_教材目录(Textbook)", "output", "matches_kg_relations.json"
)


class MatchesKGImporter:
    """MATCHES_KG 关系导入器"""

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

        matched = [r for r in data if r.get('matched')]
        unmatched = [r for r in data if not r.get('matched')]
        logger.info(f"加载数据: {len(data)} 条匹配记录（{len(matched)} 已匹配, {len(unmatched)} 未匹配）")
        return data

    def clear_relations(self):
        logger.warning("清除已有的 MATCHES_KG 关系...")
        with self.client.session() as session:
            result = session.run("MATCH ()-[r:MATCHES_KG]->() DELETE r RETURN count(r) AS deleted")
            deleted = result.single()["deleted"]
            logger.info(f"已删除 {deleted} 个 MATCHES_KG 关系")

    def import_matches_kg_relations(self, data: List[Dict], dry_run: bool = False) -> int:
        """
        创建 MATCHES_KG 关系（TextbookKP → Concept）
        仅导入 matched=true 的记录
        """
        relations = []
        for r in data:
            if r.get('matched') and r.get('kg_uri'):
                relations.append({
                    'textbook_kp_uri': r['textbook_kp_uri'],
                    'kg_uri': r['kg_uri'],
                    'confidence': r.get('confidence', 0.0),
                    'method': r.get('method', 'unknown'),
                    'textbook_kp_name': r.get('textbook_kp_name', ''),
                    'kg_name': r.get('kg_name', ''),
                })

        if not relations:
            logger.info("没有已匹配的记录需要导入")
            return 0

        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(relations)} 个 MATCHES_KG 关系 ===\n")
            for rel in relations[:3]:
                print(f"MATCH (kp:TextbookKP {{uri: '{rel['textbook_kp_uri']}'}}) MATCH (c:Concept {{uri: '{rel['kg_uri']}'}}) MERGE (kp)-[r:MATCHES_KG]->(c) SET r.confidence={rel['confidence']}, r.method='{rel['method']}';")
            logger.info(f"  ... 共 {len(relations)} 条")
            return len(relations)

        logger.info(f"\n=== 创建 {len(relations)} 个 MATCHES_KG 关系 ===")

        cypher = """
        UNWIND $relations AS rel
        MATCH (kp:TextbookKP {uri: rel.textbook_kp_uri})
        MATCH (c:Concept {uri: rel.kg_uri})
        MERGE (kp)-[r:MATCHES_KG]->(c)
        SET r.confidence = rel.confidence,
            r.method = rel.method
        """

        with self.client.session() as session:
            session.run(cypher, relations=relations)

        with self.client.session() as session:
            result = session.run("MATCH ()-[r:MATCHES_KG]->() RETURN count(r) AS count")
            count = result.single()["count"]

        logger.info(f"✓ 已创建 {count} 个 MATCHES_KG 关系")

        # 统计方法分布
        with self.client.session() as session:
            result = session.run("""
                MATCH ()-[r:MATCHES_KG]->()
                RETURN r.method AS method, count(r) AS cnt, avg(r.confidence) AS avg_conf
                ORDER BY cnt DESC
            """)
            for row in result:
                logger.info(f"  {row['method']}: {row['cnt']} 条, 平均置信度={row['avg_conf']:.3f}")

        return count

    def show_statistics(self):
        with self.client.session() as session:
            result = session.run("MATCH ()-[r:MATCHES_KG]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]

            # 按方法分布
            result = session.run("""
                MATCH ()-[r:MATCHES_KG]->()
                RETURN r.method AS method, count(r) AS cnt
                ORDER BY cnt DESC
            """)
            by_method = {r["method"]: r["cnt"] for r in result}

            # 按置信度区间分布
            result = session.run("""
                MATCH ()-[r:MATCHES_KG]->()
                WITH r,
                    CASE
                        WHEN r.confidence >= 0.9 THEN '0.9-1.0'
                        WHEN r.confidence >= 0.8 THEN '0.8-0.9'
                        WHEN r.confidence >= 0.7 THEN '0.7-0.8'
                        ELSE '<0.7'
                    END AS bucket
                RETURN bucket, count(*) AS cnt
                ORDER BY bucket DESC
            """)
            by_confidence = {r["bucket"]: r["cnt"] for r in result}

            # 没有匹配关系的知识点数量
            result = session.run("MATCH (k:TextbookKP) WHERE NOT (k)-[:MATCHES_KG]->() RETURN count(k) AS count")
            unlinked = result.single()["count"]

        logger.info("\n=== MATCHES_KG 关系导入统计 ===")
        logger.info(f"  MATCHES_KG 关系数: {rel_count}")
        logger.info(f"  按方法分布: {by_method}")
        logger.info(f"  按置信度区间分布: {by_confidence}")
        logger.info(f"  未关联的 TextbookKP: {unlinked}")

    def show_samples(self, limit: int = 10):
        logger.info(f"\n=== MATCHES_KG 关系示例（前 {limit} 个） ===")
        with self.client.session() as session:
            result = session.run("""
                MATCH (kp:TextbookKP)-[r:MATCHES_KG]->(c:Concept)
                RETURN kp.label AS kp, c.label AS concept, r.confidence AS conf, r.method AS method
                ORDER BY r.confidence DESC
                LIMIT $limit
            """, limit=limit)
            for row in result:
                logger.info(f"  {row['kp']} → MATCHES_KG(conf={row['conf']:.2f}, method={row['method']}) → {row['concept']}")


def main():
    parser = argparse.ArgumentParser(description='导入知识点匹配关系到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅打印 Cypher 语句，不执行')
    parser.add_argument('--clear', action='store_true', help='导入前清除已有的 MATCHES_KG 关系')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')

    args = parser.parse_args()
    data_file = args.file if args.file else DATA_FILE

    importer = MatchesKGImporter()

    try:
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        if args.stats:
            importer.show_statistics()
            return

        data = importer.load_data(data_file)

        if args.dry_run:
            importer.import_matches_kg_relations(data, dry_run=True)
            return

        if args.clear:
            importer.clear_relations()

        importer.import_matches_kg_relations(data)
        importer.show_statistics()
        importer.show_samples()

        logger.info("\n✅ MATCHES_KG 关系导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
