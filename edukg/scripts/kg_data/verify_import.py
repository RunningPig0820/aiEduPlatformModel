#!/usr/bin/env python3
"""验证 Neo4j 导入情况"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
sys.path.insert(0, AI_SERVICE_DIR)
os.chdir(AI_SERVICE_DIR)

from edukg.core.neo4j.client import Neo4jClient
from edukg.config.settings import settings

client = Neo4jClient()

print(f"=== Neo4j 导入验证 ===\n")
print(f"连接: {settings.NEO4J_URI}\n")

with client.session() as session:
    # 1. Concept 总数
    result = session.run("MATCH (c:Concept) RETURN count(c) AS count")
    total_concepts = result.single()['count']
    print(f"1. Concept 总数: {total_concepts}")

    # 2. v0.2 版本的 Concept (小学新增)
    result = session.run("""
        MATCH (c:Concept)
        WHERE c.uri CONTAINS '0.2'
        RETURN c.uri AS uri, c.label AS label
        ORDER BY c.label
    """)
    v02_concepts = list(result)
    print(f"\n2. 小学新增 Concept (v0.2): {len(v02_concepts)} 个")
    for c in v02_concepts[:10]:
        print(f"   - {c['label']}")
    if len(v02_concepts) > 10:
        print(f"   ... 还有 {len(v02_concepts) - 10} 个")

    # 3. 检查重复 URI
    result = session.run("""
        MATCH (c:Concept)
        WITH c.uri AS uri, count(c) AS cnt
        WHERE cnt > 1
        RETURN uri, cnt
        ORDER BY cnt DESC
        LIMIT 10
    """)
    duplicates = list(result)
    print(f"\n3. 重复 URI 检查:")
    if duplicates:
        print(f"   ❌ 发现 {len(duplicates)} 个重复 URI:")
        for d in duplicates:
            print(f"   - {d['uri']}: {d['cnt']} 次")
    else:
        print(f"   ✅ 无重复 URI")

    # 4. 无类型的 Concept
    result = session.run("""
        MATCH (c:Concept)
        WHERE NOT (c)-[:HAS_TYPE]->()
        RETURN c.label AS label, c.uri AS uri
        ORDER BY c.label
        LIMIT 15
    """)
    no_type = list(result)

    result = session.run("""
        MATCH (c:Concept)
        WHERE NOT (c)-[:HAS_TYPE]->()
        RETURN count(c) AS count
    """)
    no_type_count = result.single()['count']

    print(f"\n4. 无类型的 Concept:")
    print(f"   数量: {no_type_count}")
    for c in no_type[:15]:
        version = "v0.2" if "0.2" in c['uri'] else "v0.1"
        print(f"   - {c['label']} ({version})")

    # 5. 统计 v0.1 vs v0.2
    result = session.run("""
        MATCH (c:Concept)
        RETURN
            CASE WHEN c.uri CONTAINS '0.2' THEN 'v0.2 (小学)' ELSE 'v0.1 (EduKG)' END AS version,
            count(c) AS count
        ORDER BY version
    """)
    version_stats = list(result)
    print(f"\n5. URI 版本分布:")
    for v in version_stats:
        print(f"   {v['version']}: {v['count']} 个")

client.close()
print("\n✅ 验证完成")