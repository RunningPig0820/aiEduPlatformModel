#!/usr/bin/env python3
"""
完整导入 EDUKG 数据到 Neo4j

导入内容：
1. 所有 TTL 文件（三元组/关系数据）
2. 所有实体 JSON 文件
3. 本体文件 (ontology.owl)
"""
import os
import json
import sys
import re
from rdflib import Graph, URIRef, Literal
from tqdm import tqdm

# 添加项目根目录到 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 添加 ai-edu-ai-service 目录到 sys.path 以加载 config
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

from edukg.core.neo4j.client import Neo4jClient
from config.settings import settings

# 数据目录 (相对路径：脚本在 scripts/kg_data/，数据在 ../../data/edukg/)
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg")
TTL_DIR = os.path.join(DATA_DIR, "ttl")
ENTITIES_DIR = os.path.join(DATA_DIR, "entities")


class EDUKGImporter:
    """EDUKG 数据导入器"""

    def __init__(self):
        self.client = Neo4jClient()
        print(f"✅ 已连接 Neo4j: {settings.NEO4J_URI}")

    def close(self):
        self.client.close()

    def clear_database(self):
        """清空数据库（危险操作）"""
        # 仅允许在非生产环境或显式确认后操作
        if settings.DEBUG:
            confirm = input("⚠️  确定要清空数据库吗？(yes/no): ")
            if confirm.lower() == "yes":
                with self.client.session() as session:
                    session.run("MATCH (n) DETACH DELETE n")
                    print("⚠️  数据库已清空")
            else:
                print("❌ 操作已取消")
        else:
            print("❌ 生产环境禁止清空数据库操作")

    def create_indexes(self):
        """创建索引"""
        print("\n📌 创建索引...")
        indexes = [
            "CREATE INDEX entity_uri_index IF NOT EXISTS FOR (e:Entity) ON (e.uri)",
            "CREATE INDEX entity_label_index IF NOT EXISTS FOR (e:Entity) ON (e.label)",
            "CREATE INDEX entity_subject_index IF NOT EXISTS FOR (e:Entity) ON (e.subject)",
            "CREATE INDEX class_uri_index IF NOT EXISTS FOR (c:Class) ON (c.uri)",
            "CREATE INDEX property_uri_index IF NOT EXISTS FOR (p:Property) ON (p.uri)",
        ]
        with self.client.session() as session:
            for idx in indexes:
                session.run(idx)
        print("  索引创建完成")

    def import_ttl_file(self, ttl_file: str, subject: str = None):
        """
        导入单个 TTL 文件

        Args:
            ttl_file: TTL 文件路径
            subject: 学科名称（用于标记实体）
        """
        if not os.path.exists(ttl_file):
            print(f"  ⚠️  文件不存在: {ttl_file}")
            return 0, 0

        filename = os.path.basename(ttl_file)
        print(f"\n📥 解析 {filename}...")

        # 使用 rdflib 解析 TTL
        g = Graph()
        try:
            g.parse(ttl_file, format="turtle")
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            return 0, 0

        triple_count = len(g)
        print(f"  三元组数: {triple_count:,}")

        if triple_count == 0:
            return 0, 0

        # 提取实体和关系
        entities = {}  # {uri: {label, types, properties}}
        relations = []  # [(from_uri, relation, to_uri)]

        for s, p, o in g:
            s_uri = str(s)
            p_uri = str(p)

            # 提取实体
            if s_uri not in entities:
                entities[s_uri] = {"uri": s_uri, "label": "", "types": [], "properties": {}}

            # 处理谓词
            if "rdf-syntax-ns#type" in p_uri:
                # 类型关系
                type_name = self._extract_name(str(o))
                entities[s_uri]["types"].append(type_name)
            elif "rdf-schema#label" in p_uri:
                # 标签
                entities[s_uri]["label"] = str(o)
            elif isinstance(o, Literal):
                # 属性值
                prop_name = self._extract_name(p_uri)
                entities[s_uri]["properties"][prop_name] = str(o)
            elif isinstance(o, URIRef):
                # 关系
                rel_name = self._extract_name(p_uri)
                relations.append((s_uri, rel_name, str(o)))

                # 确保目标实体也存在
                if str(o) not in entities:
                    entities[str(o)] = {"uri": str(o), "label": "", "types": [], "properties": {}}

        # 添加学科标记
        if subject:
            for uri in entities:
                entities[uri]["subject"] = subject

        # 导入实体
        entity_count = self._import_entities(entities, subject)
        relation_count = self._import_relations(relations)

        print(f"  ✅ 导入完成: {entity_count:,} 实体, {relation_count:,} 关系")
        return entity_count, relation_count

    def _extract_name(self, uri: str) -> str:
        """从 URI 提取名称"""
        if "#" in uri:
            return uri.split("#")[-1]
        if "/" in uri:
            return uri.split("/")[-1]
        return uri

    def _import_entities(self, entities: dict, subject: str = None) -> int:
        """导入实体到 Neo4j"""
        if not entities:
            return 0

        batch_size = 500
        entity_list = list(entities.values())
        imported = 0

        with self.client.session() as session:
            for i in range(0, len(entity_list), batch_size):
                batch = entity_list[i:i+batch_size]

                query = """
                UNWIND $entities AS ent
                MERGE (e:Entity {uri: ent.uri})
                SET e.label = ent.label
                """
                params = {"entities": batch}

                if subject:
                    query += "\nSET e.subject = $subject"
                    params["subject"] = subject

                # 添加属性
                query += "\nSET e += ent.properties"

                session.run(query, params)
                imported += len(batch)

        return imported

    def _import_relations(self, relations: list) -> int:
        """导入关系到 Neo4j"""
        if not relations:
            return 0

        batch_size = 500
        imported = 0

        with self.client.session() as session:
            for i in range(0, len(relations), batch_size):
                batch = relations[i:i+batch_size]

                # 分组关系类型
                for s_uri, rel_name, o_uri in batch:
                    # 清理关系名称（去除特殊字符）
                    rel_type = re.sub(r'[^a-zA-Z0-9_]', '_', rel_name)[:50]

                    try:
                        query = f"""
                        MATCH (s:Entity {{uri: $s_uri}})
                        MATCH (o:Entity {{uri: $o_uri}})
                        MERGE (s)-[r:{rel_type}]->(o)
                        """
                        session.run(query, {"s_uri": s_uri, "o_uri": o_uri})
                        imported += 1
                    except Exception:
                        pass  # 跳过无效关系

        return imported

    def import_entities_json(self, subject: str) -> int:
        """从 JSON 文件导入实体"""
        json_file = os.path.join(ENTITIES_DIR, f"{subject}_entities.json")

        if not os.path.exists(json_file):
            return 0

        with open(json_file, "r", encoding="utf-8") as f:
            entities = json.load(f)

        if not entities:
            return 0

        print(f"  📥 导入 {subject} 实体: {len(entities):,} 个")

        batch_size = 500
        imported = 0

        with self.client.session() as session:
            for i in range(0, len(entities), batch_size):
                batch = entities[i:i+batch_size]

                query = """
                UNWIND $entities AS entity
                MERGE (e:Entity {uri: entity.uri})
                SET e.label = entity.label, e.subject = $subject
                """
                session.run(query, entities=batch, subject=subject)
                imported += len(batch)

        return imported

    def get_statistics(self):
        """获取统计信息"""
        with self.client.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count")
            node_count = result.single()["count"]

            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]

            result = session.run("""
                MATCH (e:Entity)
                WHERE e.subject IS NOT NULL
                RETURN e.subject AS subject, count(e) AS count
                ORDER BY count DESC
            """)
            subject_counts = list(result)

        print("\n" + "="*60)
        print("📊 数据库统计")
        print("="*60)
        print(f"节点总数: {node_count:,}")
        print(f"关系总数: {rel_count:,}")
        print("\n各学科实体:")
        for row in subject_counts:
            print(f"  {row['subject']}: {row['count']:,}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="EDUKG 完整数据导入")
    parser.add_argument("--clear", action="store_true", help="清空数据库")
    args = parser.parse_args()

    print("="*60)
    print("EDUKG 完整数据导入")
    print("="*60)

    importer = EDUKGImporter()

    try:
        if args.clear:
            importer.clear_database()
            return

        # 1. 创建索引
        importer.create_indexes()

        # 2. 导入 TTL 文件（包含关系数据）
        print("\n" + "="*60)
        print("📥 导入 TTL 文件")
        print("="*60)

        ttl_files = [
            ("math.ttl", "math"),
            ("physics.ttl", "physics"),
            ("chemistry.ttl", "chemistry"),
            ("biology.ttl", "biology"),
            ("chinese.ttl", "chinese"),
            ("history.ttl", "history"),
            ("geo.ttl", "geo"),
            ("politics.ttl", "politics"),
            ("english.ttl", "english"),
            ("all_concept.ttl", None),
            ("all_category.ttl", None),
        ]

        total_entities = 0
        total_relations = 0

        for filename, subject in ttl_files:
            filepath = os.path.join(TTL_DIR, filename)
            if os.path.exists(filepath):
                e_count, r_count = importer.import_ttl_file(filepath, subject)
                total_entities += e_count
                total_relations += r_count

        # 3. 统计
        importer.get_statistics()

        print("\n" + "="*60)
        print("✅ 导入完成！")
        print("="*60)
        print(f"总实体数: {total_entities:,}")
        print(f"总关系数: {total_relations:,}")
        print(f"\nNeo4j Browser: {settings.NEO4J_HTTP_URI}")

    finally:
        importer.close()


if __name__ == "__main__":
    main()