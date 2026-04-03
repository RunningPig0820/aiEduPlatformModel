#!/usr/bin/env python3
"""
导入数学知识点的 partOf 和 belongsTo 关系到 Neo4j

功能：
1. 从 math_instance.ttl 解析 partOf 和 belongsTo 关系
2. 导入为 PART_OF 和 BELONGS_TO 关系
3. 支持重复导入（使用 MERGE）

数据来源：
    edukg/data/edukg/math/2_知识点实体(Instance)/知识点实例 _类型标签/math_instance.ttl

使用方法：
    python import_partof_belongsto.py
    python import_partof_belongsto.py --dry-run
    python import_partof_belongsto.py --stats
"""
import os
import sys
import re
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Dict

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
from config.settings import settings

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
    "2_知识点实体(Instance)", "知识点实例 _类型标签", "math_instance.ttl"
)


class PartOfBelongsToImporter:
    """partOf 和 belongsTo 关系导入器"""

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

    def parse_ttl(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        解析 TTL 文件，提取 partOf 和 belongsTo 关系

        Returns:
            {
                'partOf': [(from_uri, to_uri), ...],
                'belongsTo': [(from_uri, to_uri), ...]
            }
        """
        if not os.path.exists(DATA_FILE):
            raise FileNotFoundError(f"数据文件不存在: {DATA_FILE}")

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析所有关系
        partof_relations = []
        belongsto_relations = []

        # 按行解析
        lines = content.split('\n')
        current_subject = None

        for line in lines:
            # 提取主体 URI（行首的完整 URI）
            subject_match = re.match(r'<(http://edukg\.org/knowledge/0\.1/instance/math#\d+)>', line)
            if subject_match:
                current_subject = subject_match.group(1)

            # 提取 partOf 关系
            partof_matches = re.findall(r'ns3:partOf\s+<(http://edukg\.org/knowledge/0\.1/instance/math#\d+)>', line)
            for obj_uri in partof_matches:
                if current_subject:
                    partof_relations.append((current_subject, obj_uri))

            # 提取 belongsTo 关系
            belongsto_matches = re.findall(r'ns3:belongsTo\s+<(http://edukg\.org/knowledge/0\.1/instance/math#\d+)>', line)
            for obj_uri in belongsto_matches:
                if current_subject:
                    belongsto_relations.append((current_subject, obj_uri))

        logger.info(f"解析完成: partOf={len(partof_relations)}, belongsTo={len(belongsto_relations)}")

        return {
            'partOf': partof_relations,
            'belongsTo': belongsto_relations
        }

    def import_relations(self, relations: List[Tuple[str, str]], rel_type: str, batch_size: int = 500) -> int:
        """
        导入关系到 Neo4j

        Args:
            relations: [(from_uri, to_uri), ...]
            rel_type: PART_OF 或 BELONGS_TO
            batch_size: 批量大小

        Returns:
            创建的关系数量
        """
        logger.info(f"\n=== 导入 {len(relations)} 个 {rel_type} 关系 ===")

        # 构建批量数据
        rel_data = [{'from_uri': r[0], 'to_uri': r[1]} for r in relations]

        imported = 0
        skipped = 0

        with self.client.session() as session:
            for i in range(0, len(rel_data), batch_size):
                batch = rel_data[i:i + batch_size]

                cypher = f"""
                UNWIND $relations AS rel
                MATCH (from:Entity {{uri: rel.from_uri}})
                MATCH (to:Entity {{uri: rel.to_uri}})
                MERGE (from)-[r:{rel_type}]->(to)
                """

                result = session.run(cypher, relations=batch)

                # 检查是否有匹配失败的情况
                # 由于 MERGE 不返回统计，我们需要单独统计
                imported += len(batch)

                if (i // batch_size + 1) % 3 == 0:
                    logger.info(f"  已处理 {imported}/{len(relations)} 个关系...")

        # 统计实际创建的关系数
        with self.client.session() as session:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count")
            actual_count = result.single()["count"]

        logger.info(f"✓ {rel_type} 关系导入完成: 实际创建 {actual_count} 个")
        return actual_count

    def show_statistics(self):
        """显示统计信息"""
        with self.client.session() as session:
            # PART_OF 关系统计
            result = session.run("MATCH ()-[r:PART_OF]->() RETURN count(r) AS count")
            partof_count = result.single()["count"]

            # BELONGS_TO 关系统计
            result = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS count")
            belongsto_count = result.single()["count"]

            # 示例关系
            result = session.run("""
                MATCH (from:Entity)-[r:PART_OF]->(to:Entity)
                RETURN from.label AS from_label, to.label AS to_label
                LIMIT 5
            """)
            partof_samples = list(result)

            result = session.run("""
                MATCH (from:Entity)-[r:BELONGS_TO]->(to:Entity)
                RETURN from.label AS from_label, to.label AS to_label
                LIMIT 5
            """)
            belongsto_samples = list(result)

        logger.info("\n=== 统计信息 ===")
        logger.info(f"  PART_OF 关系总数: {partof_count}")
        logger.info(f"  BELONGS_TO 关系总数: {belongsto_count}")

        logger.info("\n  PART_OF 示例:")
        for row in partof_samples:
            logger.info(f"    {row['from_label']} → PART_OF → {row['to_label']}")

        logger.info("\n  BELONGS_TO 示例:")
        for row in belongsto_samples:
            logger.info(f"    {row['from_label']} → BELONGS_TO → {row['to_label']}")

    def show_sample_from_ttl(self, limit: int = 10):
        """显示 TTL 文件中的示例"""
        logger.info(f"\n=== TTL 文件示例 (前{limit}个) ===")

        data = self.parse_ttl()

        logger.info("\n  partOf 示例:")
        for i, (from_uri, to_uri) in enumerate(data['partOf'][:limit], 1):
            from_id = re.search(r'#(\d+)', from_uri).group(1)
            to_id = re.search(r'#(\d+)', to_uri).group(1)
            logger.info(f"    {i}. Entity #{from_id} → partOf → Entity #{to_id}")

        logger.info("\n  belongsTo 示例:")
        for i, (from_uri, to_uri) in enumerate(data['belongsTo'][:limit], 1):
            from_id = re.search(r'#(\d+)', from_uri).group(1)
            to_id = re.search(r'#(\d+)', to_uri).group(1)
            logger.info(f"    {i}. Entity #{from_id} → belongsTo → Entity #{to_id}")


def main():
    parser = argparse.ArgumentParser(description='导入 partOf 和 belongsTo 关系到 Neo4j')
    parser.add_argument('--dry-run', action='store_true', help='仅打印信息，不执行导入')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')
    parser.add_argument('--batch-size', type=int, default=500, help='批量导入大小')

    args = parser.parse_args()

    importer = PartOfBelongsToImporter()

    try:
        # 测试连接
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        # 仅显示统计
        if args.stats:
            importer.show_statistics()
            return

        # 解析 TTL 文件
        relations = importer.parse_ttl()

        # Dry-run 模式
        if args.dry_run:
            logger.info(f"[DRY-RUN] 将导入:")
            logger.info(f"  - {len(relations['partOf'])} 个 PART_OF 关系")
            logger.info(f"  - {len(relations['belongsTo'])} 个 BELONGS_TO 关系")
            importer.show_sample_from_ttl()
            return

        # 导入 PART_OF 关系
        importer.import_relations(relations['partOf'], 'PART_OF', args.batch_size)

        # 导入 BELONGS_TO 关系
        importer.import_relations(relations['belongsTo'], 'BELONGS_TO', args.batch_size)

        # 显示统计
        importer.show_statistics()

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