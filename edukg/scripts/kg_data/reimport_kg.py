#!/usr/bin/env python3
"""
重新导入数学知识图谱到 Neo4j

按照 URI 前缀区分：
- instance/math#xxx → Concept (概念/知识点)
- statement/math#xxx → Statement (定义/定理描述)

使用方法：
    python reimport_kg.py
    python reimport_kg.py --stats
"""
import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
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

# 数据文件路径
CLASS_FILE = os.path.join(PROJECT_ROOT, "edukg/data/edukg/math/1_概念类(Class)/math_classes.json")
ENTITIES_FILE = os.path.join(PROJECT_ROOT, "edukg/data/edukg/math/8_全部关联关系(Complete)/math_entities_complete.json")
STATEMENT_FILE = os.path.join(PROJECT_ROOT, "edukg/data/edukg/math/3_定义_定理(Statement)/math_statement.json")
INSTANCE_TTL = os.path.join(PROJECT_ROOT, "edukg/data/edukg/math/2_知识点实体(Instance)/知识点实例 _类型标签/math_instance.ttl")
RELATIONS_FILE = os.path.join(PROJECT_ROOT, "edukg/data/edukg/math/8_全部关联关系(Complete)/math_knowledge_relations.json")


class KGImporter:
    """知识图谱导入器"""

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

    def import_classes(self, batch_size: int = 100) -> int:
        """导入概念类"""
        logger.info("\n=== 导入概念类 (Class) ===")

        with open(CLASS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        classes = data.get('classes', data)  # 兼容两种格式
        if isinstance(classes, dict):
            classes = list(classes.values())

        logger.info(f"加载数据: {len(classes)} 个概念类")

        with self.client.session() as session:
            for i in range(0, len(classes), batch_size):
                batch = classes[i:i + batch_size]

                cypher = """
                UNWIND $classes AS c
                MERGE (class:Class {uri: c.uri})
                SET class.label = c.label
                """

                session.run(cypher, classes=batch)

        # 导入 SUB_CLASS_OF 关系
        parent_relations = []
        for c in classes:
            if c.get('parents'):
                for parent_uri in c['parents']:
                    parent_relations.append({
                        'child_uri': c['uri'],
                        'parent_uri': parent_uri
                    })

        logger.info(f"SUB_CLASS_OF 关系: {len(parent_relations)}")

        with self.client.session() as session:
            for i in range(0, len(parent_relations), batch_size):
                batch = parent_relations[i:i + batch_size]
                cypher = """
                UNWIND $rels AS r
                MATCH (child:Class {uri: r.child_uri})
                MATCH (parent:Class {uri: r.parent_uri})
                MERGE (child)-[:SUB_CLASS_OF]->(parent)
                """
                session.run(cypher, rels=batch)

        with self.client.session() as session:
            result = session.run("MATCH (c:Class) RETURN count(c) AS count")
            count = result.single()["count"]

        logger.info(f"✓ 概念类导入完成: {count} 个")
        return count

    def import_entities(self, batch_size: int = 500) -> int:
        """导入知识点实体 (instance/math#xxx)"""
        logger.info("\n=== 导入知识点实体 (Concept) ===")

        with open(ENTITIES_FILE, 'r', encoding='utf-8') as f:
            all_entities = json.load(f)

        # 只导入 instance/math#xxx 前缀的实体
        entities = [e for e in all_entities if 'instance/math#' in e['uri']]
        logger.info(f"加载数据: {len(entities)} 个知识点实体 (instance 前缀)")

        with self.client.session() as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i + batch_size]

                cypher = """
                UNWIND $entities AS e
                MERGE (entity:Concept {uri: e.uri})
                SET entity.label = e.label, entity.subject = 'math'
                """

                session.run(cypher, entities=batch)

                if (i // batch_size + 1) % 3 == 0:
                    logger.info(f"  已处理 {min(i + batch_size, len(entities))}/{len(entities)}...")

        with self.client.session() as session:
            result = session.run("MATCH (e:Concept) RETURN count(e) AS count")
            count = result.single()["count"]

        logger.info(f"✓ 知识点实体导入完成: {count} 个")
        return count

    def import_statements(self, batch_size: int = 500) -> int:
        """导入定义/定理 (statement/math#xxx)"""
        logger.info("\n=== 导入定义/定理 (Statement) ===")

        with open(ENTITIES_FILE, 'r', encoding='utf-8') as f:
            all_entities = json.load(f)

        with open(STATEMENT_FILE, 'r', encoding='utf-8') as f:
            statements_data = json.load(f)

        # 只导入 statement/math#xxx 前缀的实体
        statement_entities = [e for e in all_entities if 'statement/math#' in e['uri']]
        logger.info(f"加载数据: {len(statement_entities)} 个定义/定理 (statement 前缀)")

        # 建立 URI → content 映射
        content_map = {}
        for s in statements_data:
            if s.get('content'):
                content_map[s['s']] = s['content']

        with self.client.session() as session:
            for i in range(0, len(statement_entities), batch_size):
                batch = statement_entities[i:i + batch_size]

                # 准备数据，包含 content
                batch_data = []
                for e in batch:
                    batch_data.append({
                        'uri': e['uri'],
                        'label': e['label'],
                        'content': content_map.get(e['uri'], '')
                    })

                cypher = """
                UNWIND $statements AS s
                MERGE (stmt:Statement {uri: s.uri})
                SET stmt.label = s.label, stmt.content = s.content, stmt.subject = 'math'
                """

                session.run(cypher, statements=batch_data)

                if (i // batch_size + 1) % 5 == 0:
                    logger.info(f"  已处理 {min(i + batch_size, len(statement_entities))}/{len(statement_entities)}...")

        # 统计有 content 的数量
        with self.client.session() as session:
            result = session.run("MATCH (s:Statement) RETURN count(s) AS count")
            count = result.single()["count"]

            result = session.run("MATCH (s:Statement) WHERE s.content IS NOT NULL AND s.content <> '' RETURN count(s) AS count")
            content_count = result.single()["count"]

        logger.info(f"✓ 定义/定理导入完成: {count} 个 (有 content: {content_count})")
        return count

    def import_has_type_relations(self, batch_size: int = 500) -> int:
        """导入 HAS_TYPE 关系"""
        logger.info("\n=== 导入 HAS_TYPE 关系 ===")

        with open(ENTITIES_FILE, 'r', encoding='utf-8') as f:
            all_entities = json.load(f)

        # 为 Concept 和 Statement 分别导入
        entity_types = []
        statement_types = []

        for e in all_entities:
            if not e.get('types'):
                continue

            for t in e['types']:
                type_uri = f"http://edukg.org/knowledge/0.1/class/math#{t}"
                if 'instance/math#' in e['uri']:
                    entity_types.append({'uri': e['uri'], 'type_uri': type_uri})
                elif 'statement/math#' in e['uri']:
                    statement_types.append({'uri': e['uri'], 'type_uri': type_uri})

        logger.info(f"Concept HAS_TYPE: {len(entity_types)}")
        logger.info(f"Statement HAS_TYPE: {len(statement_types)}")

        with self.client.session() as session:
            # Concept HAS_TYPE
            for i in range(0, len(entity_types), batch_size):
                batch = entity_types[i:i + batch_size]
                cypher = """
                UNWIND $rels AS r
                MATCH (e:Concept {uri: r.uri})
                MATCH (c:Class {uri: r.type_uri})
                MERGE (e)-[:HAS_TYPE]->(c)
                """
                session.run(cypher, rels=batch)

            # Statement HAS_TYPE
            for i in range(0, len(statement_types), batch_size):
                batch = statement_types[i:i + batch_size]
                cypher = """
                UNWIND $rels AS r
                MATCH (s:Statement {uri: r.uri})
                MATCH (c:Class {uri: r.type_uri})
                MERGE (s)-[:HAS_TYPE]->(c)
                """
                session.run(cypher, rels=batch)

        with self.client.session() as session:
            result = session.run("MATCH ()-[r:HAS_TYPE]->() RETURN count(r) AS count")
            count = result.single()["count"]

        logger.info(f"✓ HAS_TYPE 关系导入完成: {count} 个")
        return count

    def import_related_to_relations(self, batch_size: int = 1000) -> int:
        """导入 RELATED_TO 关系"""
        logger.info("\n=== 导入 RELATED_TO 关系 ===")

        with open(RELATIONS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        relations = data.get('relations', [])
        logger.info(f"加载数据: {len(relations)} 个关系")

        # 分类统计
        instance_to_instance = []
        statement_to_instance = []

        for r in relations:
            from_uri = r['from']['uri']
            to_uri = r['to']['uri']

            if 'instance/math#' in from_uri and 'instance/math#' in to_uri:
                instance_to_instance.append(r)
            elif 'statement/math#' in from_uri and 'instance/math#' in to_uri:
                statement_to_instance.append(r)

        logger.info(f"  instance → instance: {len(instance_to_instance)}")
        logger.info(f"  statement → instance: {len(statement_to_instance)}")

        with self.client.session() as session:
            # instance → instance
            for i in range(0, len(instance_to_instance), batch_size):
                batch = instance_to_instance[i:i + batch_size]
                cypher = """
                UNWIND $rels AS r
                MATCH (from:Concept {uri: r.from.uri})
                MATCH (to:Concept {uri: r.to.uri})
                MERGE (from)-[:RELATED_TO]->(to)
                """
                session.run(cypher, rels=batch)

            # statement → instance (定义关联到知识点)
            for i in range(0, len(statement_to_instance), batch_size):
                batch = statement_to_instance[i:i + batch_size]
                cypher = """
                UNWIND $rels AS r
                MATCH (from:Statement {uri: r.from.uri})
                MATCH (to:Concept {uri: r.to.uri})
                MERGE (from)-[:RELATED_TO]->(to)
                """
                session.run(cypher, rels=batch)

        with self.client.session() as session:
            result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count")
            count = result.single()["count"]

        logger.info(f"✓ RELATED_TO 关系导入完成: {count} 个")
        return count

    def import_partof_belongsto(self, batch_size: int = 500) -> int:
        """导入 PART_OF 和 BELONGS_TO 关系"""
        import re
        logger.info("\n=== 导入 PART_OF 和 BELONGS_TO 关系 ===")

        with open(INSTANCE_TTL, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析关系
        partof_relations = []
        belongsto_relations = []
        lines = content.split('\n')
        current_subject = None

        for line in lines:
            subject_match = re.match(r'<(http://edukg\.org/knowledge/0\.1/instance/math#\d+)>', line)
            if subject_match:
                current_subject = subject_match.group(1)

            partof_matches = re.findall(r'ns3:partOf\s+<(http://edukg\.org/knowledge/0\.1/instance/math#\d+)>', line)
            for obj_uri in partof_matches:
                if current_subject:
                    partof_relations.append((current_subject, obj_uri))

            belongsto_matches = re.findall(r'ns3:belongsTo\s+<(http://edukg\.org/knowledge/0\.1/instance/math#\d+)>', line)
            for obj_uri in belongsto_matches:
                if current_subject:
                    belongsto_relations.append((current_subject, obj_uri))

        logger.info(f"partOf: {len(partof_relations)}, belongsTo: {len(belongsto_relations)}")

        with self.client.session() as session:
            # PART_OF
            for i in range(0, len(partof_relations), batch_size):
                batch = [{'from': r[0], 'to': r[1]} for r in partof_relations[i:i + batch_size]]
                cypher = """
                UNWIND $rels AS r
                MATCH (from:Concept {uri: r.from})
                MATCH (to:Concept {uri: r.to})
                MERGE (from)-[:PART_OF]->(to)
                """
                session.run(cypher, rels=batch)

            # BELONGS_TO
            for i in range(0, len(belongsto_relations), batch_size):
                batch = [{'from': r[0], 'to': r[1]} for r in belongsto_relations[i:i + batch_size]]
                cypher = """
                UNWIND $rels AS r
                MATCH (from:Concept {uri: r.from})
                MATCH (to:Concept {uri: r.to})
                MERGE (from)-[:BELONGS_TO]->(to)
                """
                session.run(cypher, rels=batch)

        with self.client.session() as session:
            result = session.run("MATCH ()-[r:PART_OF]->() RETURN count(r) AS count")
            partof_count = result.single()["count"]

            result = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS count")
            belongsto_count = result.single()["count"]

        logger.info(f"✓ PART_OF: {partof_count}, BELONGS_TO: {belongsto_count}")
        return partof_count + belongsto_count

    def show_statistics(self):
        """显示统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("Neo4j 数据统计")
        logger.info("=" * 60)

        with self.client.session() as session:
            # 节点统计
            result = session.run("MATCH (c:Class) RETURN count(c) AS count")
            class_count = result.single()["count"]

            result = session.run("MATCH (e:Concept) RETURN count(e) AS count")
            entity_count = result.single()["count"]

            result = session.run("MATCH (s:Statement) RETURN count(s) AS count")
            statement_count = result.single()["count"]

            # 关系统计
            result = session.run("MATCH ()-[r:SUB_CLASS_OF]->() RETURN count(r) AS count")
            sub_class_of = result.single()["count"]

            result = session.run("MATCH ()-[r:HAS_TYPE]->() RETURN count(r) AS count")
            has_type = result.single()["count"]

            result = session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r) AS count")
            related_to = result.single()["count"]

            result = session.run("MATCH ()-[r:PART_OF]->() RETURN count(r) AS count")
            part_of = result.single()["count"]

            result = session.run("MATCH ()-[r:BELONGS_TO]->() RETURN count(r) AS count")
            belongs_to = result.single()["count"]

            # Statement 有 content 的数量
            result = session.run("""
                MATCH (s:Statement)
                WHERE s.content IS NOT NULL AND s.content <> ''
                RETURN count(s) AS count
            """)
            content_count = result.single()["count"]

        logger.info(f"""
┌─────────────────────────────────────────────┐
│           Neo4j 数学知识图谱                 │
├─────────────────────────────────────────────┤
│ 节点                                         │
│   Class (概念类):       {class_count}                   │
│   Concept (知识点):      {entity_count}                 │
│   Statement (定义):     {statement_count}                │
│                                              │
│ 关系                                         │
│   SUB_CLASS_OF:          {sub_class_of}               │
│   HAS_TYPE:            {has_type}              │
│   RELATED_TO:          {related_to}              │
│   PART_OF:               {part_of}               │
│   BELONGS_TO:            {belongs_to}               │
│                                              │
│ 属性                                         │
│   Statement.content:     {content_count}              │
└─────────────────────────────────────────────┘
""")

        # 示例
        logger.info("\n【Concept 示例】:")
        with self.client.session() as session:
            result = session.run("""
                MATCH (e:Concept)-[:HAS_TYPE]->(c:Class)
                RETURN e.label AS label, c.label AS type
                LIMIT 5
            """)
            for row in result:
                logger.info(f"  {row['label']} → {row['type']}")

        logger.info("\n【Statement 示例】:")
        with self.client.session() as session:
            result = session.run("""
                MATCH (s:Statement)
                WHERE s.content IS NOT NULL AND s.content <> ''
                RETURN s.label AS label, s.content AS content
                LIMIT 3
            """)
            for row in result:
                logger.info(f"  {row['label']}: {row['content'][:50]}...")

        logger.info("\n【RELATED_TO 示例 (Statement→Concept)】:")
        with self.client.session() as session:
            result = session.run("""
                MATCH (s:Statement)-[:RELATED_TO]->(e:Concept)
                RETURN s.label AS stmt, e.label AS entity
                LIMIT 5
            """)
            for row in result:
                logger.info(f"  {row['stmt']} → RELATED_TO → {row['entity']}")


def main():
    parser = argparse.ArgumentParser(description='重新导入数学知识图谱')
    parser.add_argument('--stats', action='store_true', help='仅显示统计信息')
    parser.add_argument('--skip-classes', action='store_true', help='跳过概念类导入')
    parser.add_argument('--skip-entities', action='store_true', help='跳过实体导入')
    parser.add_argument('--skip-statements', action='store_true', help='跳过定义导入')
    parser.add_argument('--skip-relations', action='store_true', help='跳过关系导入')

    args = parser.parse_args()

    importer = KGImporter()

    try:
        if not importer.test_connection():
            logger.error("Neo4j 连接失败")
            sys.exit(1)

        if args.stats:
            importer.show_statistics()
            return

        # 导入顺序
        if not args.skip_classes:
            importer.import_classes()

        if not args.skip_entities:
            importer.import_entities()

        if not args.skip_statements:
            importer.import_statements()

        if not args.skip_relations:
            importer.import_has_type_relations()
            importer.import_related_to_relations()
            importer.import_partof_belongsto()

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