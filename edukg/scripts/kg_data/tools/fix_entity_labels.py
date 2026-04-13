#!/usr/bin/env python3
"""修复 Entity 节点为 Concept"""
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

print("=== 修复 Entity → Concept ===\n")

with client.session() as session:
    # 1. 查看 Entity 节点数量
    result = session.run("MATCH (n:Entity) RETURN count(n) AS count")
    entity_count = result.single()['count']
    print(f"Entity 节点数量: {entity_count}")

    # 2. 查看 Entity 节点示例
    if entity_count > 0:
        result = session.run("""
            MATCH (n:Entity)
            RETURN n.uri AS uri, n.label AS label
            LIMIT 5
        """)
        print("\nEntity 节点示例:")
        for row in result:
            print(f"  {row['label']}: {row['uri'][:60]}...")

    # 3. 检查是否有 Entity 约束
    result = session.run("SHOW CONSTRAINTS")
    constraints = list(result)
    entity_constraints = [c for c in constraints if 'Entity' in str(c.get('labelsOrTypes', []))]
    print(f"\nEntity 相关约束: {len(entity_constraints)} 个")
    for c in entity_constraints:
        print(f"  {c.get('name', 'unknown')}")

print("\n=== 修复方案 ===")
print("1. 删除 Entity 约束")
print("2. 将 Entity 节点标签改为 Concept")

client.close()
print("\n✅ 检查完成")