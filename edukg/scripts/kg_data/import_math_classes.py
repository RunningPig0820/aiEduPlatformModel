#!/usr/bin/env python3
"""
导入数学概念类到 Neo4j

功能：
1. 导入 38 个数学概念类（Class）
2. 创建父子层级关系（SUB_CLASS_OF）
3. 创建唯一性约束

使用方法：
    python import_math_classes.py
    python import_math_classes.py --dry-run  # 仅打印 Cypher 语句
    python import_math_classes.py --clear    # 清除已有的 Class 节点
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
    "1_概念类(Class)", "math_classes.json"
)


class MathClassImporter:
    """数学概念类导入器"""

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

    def load_data(self) -> Dict[str, Any]:
        """加载 JSON 数据"""
        if not os.path.exists(DATA_FILE):
            raise FileNotFoundError(f"数据文件不存在: {DATA_FILE}")

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"加载数据: {data['subject_name']} - {data['class_count']} 个概念类")
        return data

    def create_constraints(self, dry_run: bool = False):
        """创建唯一性约束"""
        constraints = [
            # 概念类 URI 唯一
            """
            CREATE CONSTRAINT class_uri_unique IF NOT EXISTS
            FOR (c:Class) REQUIRE c.uri IS UNIQUE
            """,
            # 概念类 ID 唯一
            """
            CREATE CONSTRAINT class_id_unique IF NOT EXISTS
            FOR (c:Class) REQUIRE c.id IS UNIQUE
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

    def clear_classes(self):
        """清除已有的 Class 节点"""
        logger.warning("清除已有的 Class 节点...")
        with self.client.session() as session:
            # 先删除关系
            session.run("MATCH ()-[r:SUB_CLASS_OF]->() DELETE r")
            # 再删除节点
            result = session.run("MATCH (c:Class) DELETE c RETURN count(c) AS deleted")
            deleted = result.single()["deleted"]
            logger.info(f"已删除 {deleted} 个 Class 节点")

    def import_classes(self, classes: List[Dict], dry_run: bool = False) -> int:
        """
        导入概念类节点

        Args:
            classes: 概念类列表
            dry_run: 是否仅打印语句

        Returns:
            导入的节点数量
        """
        if dry_run:
            logger.info("\n=== DRY-RUN: 创建 Class 节点 ===\n")
            for cls in classes:
                print(f"""
MERGE (c:Class {{uri: '{cls['uri']}'}})
SET c.id = '{cls['id']}',
    c.label = '{cls['label']}',
    c.description = '{cls.get('description', '')}',
    c.subject = '{cls.get('subject', 'math')}'
;""")
            return len(classes)

        logger.info(f"\n=== 导入 {len(classes)} 个概念类节点 ===")

        cypher = """
        UNWIND $classes AS cls
        MERGE (c:Class {uri: cls.uri})
        SET c.id = cls.id,
            c.label = cls.label,
            c.description = cls.description,
            c.subject = cls.subject
        """

        with self.client.session() as session:
            session.run(cypher, classes=classes)

        logger.info(f"✓ 已导入 {len(classes)} 个概念类节点")
        return len(classes)

    def import_relationships(self, classes: List[Dict], dry_run: bool = False) -> int:
        """
        导入父子层级关系

        Args:
            classes: 概念类列表
            dry_run: 是否仅打印语句

        Returns:
            创建的关系数量
        """
        # 收集所有父子关系
        relationships = []
        for cls in classes:
            if cls.get('parents'):
                for parent_uri in cls['parents']:
                    relationships.append({
                        'child_uri': cls['uri'],
                        'parent_uri': parent_uri
                    })

        if not relationships:
            logger.info("没有父子关系需要导入")
            return 0

        if dry_run:
            logger.info(f"\n=== DRY-RUN: 创建 {len(relationships)} 个 SUB_CLASS_OF 关系 ===\n")
            for rel in relationships:
                print(f"""
MATCH (child:Class {{uri: '{rel['child_uri']}'}})
MATCH (parent:Class {{uri: '{rel['parent_uri']}'}})
MERGE (child)-[:SUB_CLASS_OF]->(parent)
;""")
            return len(relationships)

        logger.info(f"\n=== 创建 {len(relationships)} 个 SUB_CLASS_OF 关系 ===")

        # 注意：父类可能在数据中不存在（外部本体），需要处理
        cypher = """
        UNWIND $relationships AS rel
        MATCH (child:Class {uri: rel.child_uri})
        OPTIONAL MATCH (parent:Class {uri: rel.parent_uri})
        WITH child, parent, rel
        WHERE parent IS NOT NULL
        MERGE (child)-[:SUB_CLASS_OF]->(parent)
        """

        with self.client.session() as session:
            session.run(cypher, relationships=relationships)

        # 统计成功创建的关系数
        with self.client.session() as session:
            result = session.run("MATCH ()-[r:SUB_CLASS_OF]->() RETURN count(r) AS count")
            count = result.single()["count"]

        logger.info(f"✓ 已创建 {count} 个 SUB_CLASS_OF 关系")
        return count

    def show_statistics(self):
        """显示导入统计"""
        with self.client.session() as session:
            # 节点数量
            result = session.run("MATCH (c:Class) RETURN count(c) AS count")
            node_count = result.single()["count"]

            # 关系数量
            result = session.run("MATCH ()-[r:SUB_CLASS_OF]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]

            # 根节点（没有父类的节点）
            result = session.run("""
                MATCH (c:Class)
                WHERE NOT (c)-[:SUB_CLASS_OF]->()
                RETURN c.label AS label
                ORDER BY label
            """)
            root_nodes = [r["label"] for r in result]

            # 层级深度
            result = session.run("""
                MATCH path = (c:Class)-[:SUB_CLASS_OF*]->(root:Class)
                WHERE NOT (root)-[:SUB_CLASS_OF]->()
                RETURN max(length(path)) AS max_depth
            """)
            record = result.single()
            max_depth = record["max_depth"] if record else 0

        logger.info("\n=== 导入统计 ===")
        logger.info(f"  Class 节点数: {node_count}")
        logger.info(f"  SUB_CLASS_OF 关系数: {rel_count}")
        logger.info(f"  最大层级深度: {max_depth}")
        logger.info(f"  根节点: {', '.join(root_nodes) if root_nodes else '无'}")

    def show_hierarchy(self, limit: int = 20):
        """显示层级结构示例"""
        logger.info(f"\n=== 层级结构示例（前 {limit} 个） ===")

        with self.client.session() as session:
            result = session.run("""
                MATCH (c:Class)-[:SUB_CLASS_OF]->(parent:Class)
                RETURN c.label AS child, parent.label AS parent
                ORDER BY parent, child
                LIMIT $limit
            """, limit=limit)

            for row in result:
                logger.info(f"  {row['child']} → SUB_CLASS_OF → {row['parent']}")


def main():
    parser = argparse.ArgumentParser(description='导入数学概念类到 Neo4j')
    parser.add_argument('--file', type=str, help='指定数据文件路径（默认使用 math_classes.json）')
    parser.add_argument('--dry-run', action='store_true', help='仅打印 Cypher 语句，不执行')
    parser.add_argument('--clear', action='store_true', help='导入前清除已有的 Class 节点')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')

    args = parser.parse_args()

    # 确定数据文件路径
    if args.file:
        data_file = args.file if os.path.isabs(args.file) else os.path.join(PROJECT_ROOT, args.file)
    else:
        data_file = DATA_FILE

    importer = MathClassImporter()

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
            data = json.load(f)

        classes = data['classes']
        logger.info(f"加载数据文件: {data_file}")
        logger.info(f"概念类数量: {len(classes)}")

        # Dry-run 模式
        if args.dry_run:
            importer.create_constraints(dry_run=True)
            importer.import_classes(classes, dry_run=True)
            importer.import_relationships(classes, dry_run=True)
            return

        # 创建约束
        importer.create_constraints()

        # 清除已有数据
        if args.clear:
            importer.clear_classes()

        # 导入节点
        importer.import_classes(classes)

        # 导入关系
        importer.import_relationships(classes)

        # 显示统计
        importer.show_statistics()
        importer.show_hierarchy()

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