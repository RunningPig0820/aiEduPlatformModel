#!/usr/bin/env python3
"""
导入教材节点 (Textbook) 到 Neo4j

功能：
1. 导入教材节点（21 册）
2. 创建唯一性约束（uri, id）

数据来源：
    edukg/data/edukg/math/5_教材目录(Textbook)/output/textbooks.json

使用方法：
    python import_textbooks.py
    python import_textbooks.py --dry-run    # 仅打印 Cypher 语句
    python import_textbooks.py --clear      # 清除已有的 Textbook 节点
    python import_textbooks.py --stats      # 仅显示统计信息
    python import_textbooks.py --file PATH  # 指定数据文件路径
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
KG_DATA_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(KG_DATA_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 添加 ai-edu-ai-service 目录到 sys.path 以加载 config
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

# 切换工作目录到 ai-edu-ai-service 以正确加载 .env 文件
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
    "5_教材目录(Textbook)", "output", "textbooks.json"
)


class TextbookImporter:
    """教材节点导入器"""

    def __init__(self):
        self.client = Neo4jClient()
        logger.info(f"已连接 Neo4j: {settings.NEO4J_URI}")

    def close(self):
        self.client.close()

    def test_connection(self) -> bool:
        """测试 Neo4j 连接"""
        if self.client.health_check():
            version = self.client.get_version()
            logger.info(f"Neo4j 连接成功，版本: {version}")
            return True
        return False

    def load_data(self, file_path: str = None) -> List[Dict]:
        """加载 JSON 数据"""
        path = file_path or DATA_FILE
        if not os.path.exists(path):
            raise FileNotFoundError(f"数据文件不存在: {path}")

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"加载数据: {len(data)} 个教材")
        return data

    def create_constraints(self, dry_run: bool = False):
        """创建唯一性约束"""
        constraints = [
            """
            CREATE CONSTRAINT textbook_uri_unique IF NOT EXISTS
            FOR (t:Textbook) REQUIRE t.uri IS UNIQUE
            """,
            """
            CREATE CONSTRAINT textbook_id_unique IF NOT EXISTS
            FOR (t:Textbook) REQUIRE t.id IS UNIQUE
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

    def clear_textbooks(self):
        """清除已有的 Textbook 节点"""
        logger.warning("清除已有的 Textbook 节点及相关关系...")
        with self.client.session() as session:
            # 先删除 Textbook 的 CONTAINS 关系
            session.run("MATCH ()-[r:CONTAINS]->() WHERE r IS NOT NULL DELETE r")
            result = session.run("MATCH (t:Textbook) DELETE t RETURN count(t) AS deleted")
            deleted = result.single()["deleted"]
            logger.info(f"已删除 {deleted} 个 Textbook 节点")

    def import_textbooks(self, textbooks: List[Dict], dry_run: bool = False) -> int:
        """
        导入教材节点

        Args:
            textbooks: 教材列表
            dry_run: 是否仅打印语句

        Returns:
            导入的节点数量
        """
        if dry_run:
            logger.info("\n=== DRY-RUN: 创建 Textbook 节点 ===\n")
            for tb in textbooks:
                props = ", ".join(f"{k} = '{v}'" for k, v in tb.items())
                print(f"MERGE (t:Textbook {{uri: '{tb['uri']}'}}) SET {props};")
            return len(textbooks)

        logger.info(f"\n=== 导入 {len(textbooks)} 个教材节点 ===")

        cypher = """
        UNWIND $textbooks AS tb
        MERGE (t:Textbook {uri: tb.uri})
        SET t.id = tb.id,
            t.label = tb.label,
            t.stage = tb.stage,
            t.grade = tb.grade,
            t.semester = tb.semester,
            t.publisher = tb.publisher,
            t.edition = tb.edition
        """

        with self.client.session() as session:
            session.run(cypher, textbooks=textbooks)

        logger.info(f"✓ 已导入 {len(textbooks)} 个教材节点")
        return len(textbooks)

    def show_statistics(self):
        """显示导入统计"""
        with self.client.session() as session:
            result = session.run("MATCH (t:Textbook) RETURN count(t) AS count")
            node_count = result.single()["count"]

            result = session.run("MATCH (t:Textbook) RETURN t.stage AS stage, count(t) AS cnt ORDER BY stage")
            by_stage = {r["stage"]: r["cnt"] for r in result}

            result = session.run("MATCH (t:Textbook) RETURN t.label AS label ORDER BY label")
            labels = [r["label"] for r in result]

        logger.info("\n=== 教材导入统计 ===")
        logger.info(f"  Textbook 节点数: {node_count}")
        if by_stage:
            logger.info(f"  按学段分布: {by_stage}")
        if labels:
            logger.info(f"  教材列表: {', '.join(labels)}")

    def show_samples(self, limit: int = 10):
        """显示教材示例"""
        logger.info(f"\n=== 教材示例（前 {limit} 个） ===")
        with self.client.session() as session:
            result = session.run("""
                MATCH (t:Textbook)
                RETURN t.label AS label, t.stage AS stage, t.grade AS grade, t.semester AS semester
                ORDER BY t.grade, t.semester
                LIMIT $limit
            """, limit=limit)
            for row in result:
                logger.info(f"  {row['label']} ({row['stage']}/{row['grade']}/{row['semester']})")


def main():
    parser = argparse.ArgumentParser(description='导入教材节点到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径')
    parser.add_argument('--dry-run', action='store_true', help='仅打印 Cypher 语句，不执行')
    parser.add_argument('--clear', action='store_true', help='导入前清除已有的 Textbook 节点')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')

    args = parser.parse_args()

    data_file = args.file if args.file else DATA_FILE

    importer = TextbookImporter()

    try:
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        if args.stats:
            importer.show_statistics()
            return

        textbooks = importer.load_data(data_file)

        if args.dry_run:
            importer.create_constraints(dry_run=True)
            importer.import_textbooks(textbooks, dry_run=True)
            return

        importer.create_constraints()

        if args.clear:
            importer.clear_textbooks()

        importer.import_textbooks(textbooks)
        importer.show_statistics()
        importer.show_samples()

        logger.info("\n✅ 教材导入完成!")

    except Exception as e:
        logger.error(f"导入失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
