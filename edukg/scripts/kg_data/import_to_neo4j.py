#!/usr/bin/env python3
"""
EDUKG 数据导入 Neo4j 脚本

功能：
1. 解析 TTL 文件
2. 批量导入到 Neo4j
3. 支持分学科导入

使用方法：
    python import_to_neo4j.py --subject math
    python import_to_neo4j.py --all
    python import_to_neo4j.py --list
"""
import os
import argparse
import sys
from tqdm import tqdm
import json

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


class Neo4jImporter:
    """Neo4j 数据导入器"""

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
        """创建索引，提升查询性能"""
        indexes = [
            "CREATE INDEX entity_uri_index IF NOT EXISTS FOR (e:Entity) ON (e.uri)",
            "CREATE INDEX entity_label_index IF NOT EXISTS FOR (e:Entity) ON (e.label)",
            "CREATE INDEX entity_subject_index IF NOT EXISTS FOR (e:Entity) ON (e.subject)",
            "CREATE INDEX class_uri_index IF NOT EXISTS FOR (c:Class) ON (c.uri)",
            "CREATE INDEX student_id_index IF NOT EXISTS FOR (s:Student) ON (s.id)",
        ]

        with self.client.session() as session:
            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    print(f"  索引创建警告: {e}")

        print("✅ 索引创建完成")

    def import_entities_from_json(self, subject: str, limit: int = None):
        """
        从 JSON 文件导入实体（简化版，快速导入）

        Args:
            subject: 学科名称 (math, physics, etc.)
            limit: 限制导入数量，None 表示全部
        """
        json_file = os.path.join(ENTITIES_DIR, f"{subject}_entities.json")

        if not os.path.exists(json_file):
            print(f"❌ 文件不存在: {json_file}")
            return 0

        with open(json_file, "r", encoding="utf-8") as f:
            entities = json.load(f)

        if limit:
            entities = entities[:limit]

        print(f"\n📥 导入 {subject} 实体: {len(entities)} 个")

        # 批量导入
        batch_size = 500
        imported = 0

        with self.client.session() as session:
            for i in tqdm(range(0, len(entities), batch_size), desc="导入进度"):
                batch = entities[i : i + batch_size]

                # 构建批量 Cypher
                query = """
                UNWIND $entities AS entity
                MERGE (e:Entity {uri: entity.uri})
                SET e.label = entity.label,
                    e.subject = $subject
                """

                session.run(
                    query,
                    entities=batch,
                    subject=subject
                )
                imported += len(batch)

        print(f"✅ 导入完成: {imported} 个实体")
        return imported

    def import_ttl_file(self, ttl_file: str):
        """
        导入 TTL 文件到 Neo4j

        注意：此方法使用 Python 解析 TTL，适用于无法安装 n10s 插件的情况
        """
        if not os.path.exists(ttl_file):
            print(f"❌ 文件不存在: {ttl_file}")
            return

        print(f"\n📥 解析 TTL 文件: {ttl_file}")

        # 读取 TTL 文件
        with open(ttl_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析三元组（简化版）
        # 格式: <subject> <predicate> <object> .
        triples = []
        lines = content.split("\n")

        current_subject = None
        current_predicate = None

        for line in lines:
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith("@prefix") or line.startswith("@base"):
                continue

            # 解析三元组（简化处理）
            if line.startswith("<"):
                # 新的三元组开始
                parts = line.split()
                if len(parts) >= 3:
                    subject = parts[0].strip("<>")
                    predicate = parts[1].strip("<>")
                    obj = " ".join(parts[2:]).rstrip(" .;")

                    triples.append({
                        "subject": subject,
                        "predicate": predicate,
                        "object": obj
                    })

        print(f"  解析到 {len(triples)} 个三元组")

        # TODO: 实现三元组导入逻辑
        # 这需要更复杂的解析逻辑来处理 RDF 格式

    def get_statistics(self):
        """获取数据库统计信息"""
        with self.client.session() as session:
            # 节点数量
            result = session.run("MATCH (n) RETURN count(n) AS count")
            node_count = result.single()["count"]

            # 关系数量
            result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
            rel_count = result.single()["count"]

            # 各学科实体数量
            result = session.run("""
                MATCH (e:Entity)
                RETURN e.subject AS subject, count(e) AS count
                ORDER BY count DESC
            """)
            subject_counts = list(result)

        print("\n📊 数据库统计:")
        print(f"  节点总数: {node_count:,}")
        print(f"  关系总数: {rel_count:,}")
        print("\n  各学科实体:")
        for row in subject_counts:
            print(f"    {row['subject']}: {row['count']:,}")

    def list_available_data(self):
        """列出可导入的数据"""
        print("\n📁 可导入的数据文件:")
        print("\n【实体 JSON 文件】")
        if os.path.exists(ENTITIES_DIR):
            for f in sorted(os.listdir(ENTITIES_DIR)):
                if f.endswith(".json"):
                    filepath = os.path.join(ENTITIES_DIR, f)
                    size = os.path.getsize(filepath) / 1024
                    print(f"  {f} ({size:.1f} KB)")

        print("\n【TTL 文件】")
        if os.path.exists(TTL_DIR):
            for f in sorted(os.listdir(TTL_DIR)):
                if f.endswith(".ttl"):
                    filepath = os.path.join(TTL_DIR, f)
                    size = os.path.getsize(filepath) / 1024
                    print(f"  {f} ({size:.1f} KB)")


def main():
    parser = argparse.ArgumentParser(description="EDUKG 数据导入 Neo4j")
    parser.add_argument("--subject", "-s", help="导入指定学科 (math, physics, etc.)")
    parser.add_argument("--all", "-a", action="store_true", help="导入所有学科")
    parser.add_argument("--list", "-l", action="store_true", help="列出可导入的数据")
    parser.add_argument("--stats", action="store_true", help="显示数据库统计")
    parser.add_argument("--clear", action="store_true", help="清空数据库（谨慎使用）")
    parser.add_argument("--limit", type=int, help="限制导入数量")

    args = parser.parse_args()

    importer = Neo4jImporter()

    try:
        if args.list:
            importer.list_available_data()

        elif args.stats:
            importer.get_statistics()

        elif args.clear:
            importer.clear_database()

        elif args.all:
            # 导入所有学科
            subjects = ["math", "physics", "chemistry", "biology", "chinese",
                       "history", "geo", "politics", "english"]

            print("🚀 开始导入所有学科...")
            importer.create_indexes()

            total = 0
            for subject in subjects:
                count = importer.import_entities_from_json(subject, args.limit)
                total += count

            print(f"\n✅ 全部导入完成: {total} 个实体")
            importer.get_statistics()

        elif args.subject:
            # 导入指定学科
            importer.create_indexes()
            importer.import_entities_from_json(args.subject, args.limit)
            importer.get_statistics()

        else:
            parser.print_help()

    finally:
        importer.close()


if __name__ == "__main__":
    main()