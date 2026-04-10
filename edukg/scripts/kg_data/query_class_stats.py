#!/usr/bin/env python3
"""查询 Class 关联数量排名"""
import os
import sys

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

client = Neo4jClient()

print("=== 各 Class 关联数量排名 (HAS_TYPE) ===\n")

with client.session() as session:
    # 各 Class 关联数量排名
    result = session.run("""
        MATCH (n)-[:HAS_TYPE]->(c:Class)
        RETURN c.label AS label, count(n) AS count
        ORDER BY count DESC
        LIMIT 15
    """)
    for row in result:
        print(f"  {row['label']}: {row['count']} 个节点")

    # 数学定义详细信息
    print("\n=== 数学定义 详细信息 ===")
    result = session.run("""
        MATCH (c:Class)
        WHERE c.label CONTAINS "数学定义" OR c.uri CONTAINS "shuxuedingyi"
        RETURN c.uri AS uri, c.label AS label
    """)
    for c in result:
        uri = c['uri']
        label = c['label']
        print(f"\nURI: {uri}")
        print(f"Label: {label}")

        # Statement 数量
        r2 = session.run("""
            MATCH (s:Statement)-[:HAS_TYPE]->(c:Class {uri: $uri})
            RETURN count(s) AS count
        """, uri=uri)
        stmt_count = r2.single()['count']

        # Concept 数量
        r3 = session.run("""
            MATCH (c2:Concept)-[:HAS_TYPE]->(c:Class {uri: $uri})
            RETURN count(c2) AS count
        """, uri=uri)
        concept_count = r3.single()['count']

        print(f"关联 Statement: {stmt_count}")
        print(f"关联 Concept: {concept_count}")
        print(f"总计: {stmt_count + concept_count}")

        # 小学部分
        r4 = session.run("""
            MATCH (s:Statement)-[:HAS_TYPE]->(c:Class {uri: $uri})
            WHERE s.uri CONTAINS "0.2"
            RETURN count(s) AS count
        """, uri=uri)
        v02_count = r4.single()['count']
        print(f"小学 Statement (v0.2): {v02_count}")

client.close()
print("\n✅ 查询完成")