#!/usr/bin/env python3
"""验证小学关系数据"""
import os
import sys
import json

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

# 加载关系数据
DATA_FILE = os.path.join(
    PROJECT_ROOT,
    "edukg", "data", "edukg", "math",
    "4_知识点关联关系(Relation)", "primary_math_relations.json"
)

with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

relations = data['relations']
print(f"总关系数: {len(relations)}")

client = Neo4jClient()

# 统计 URI 类型
from_statements = set()
to_instances = set()
to_classes = set()
missing_from = []
missing_to = []

with client.session() as session:
    for r in relations:
        from_uri = r['from']['uri']
        to_uri = r['to']['uri']

        # from 应该是 Statement
        if 'statement' in from_uri:
            from_statements.add(from_uri)
            result = session.run(
                'MATCH (s:Statement {uri: $uri}) RETURN count(s) AS count',
                uri=from_uri
            )
            if result.single()['count'] == 0:
                missing_from.append(r['from']['label'])

        # to 可能是 Concept (instance) 或 Class
        if '/instance/' in to_uri:
            to_instances.add(to_uri)
            result = session.run(
                'MATCH (c:Concept {uri: $uri}) RETURN count(c) AS count',
                uri=to_uri
            )
            if result.single()['count'] == 0:
                missing_to.append((r['to']['label'], 'Concept'))
        elif '/class/' in to_uri:
            to_classes.add(to_uri)
            result = session.run(
                'MATCH (c:Class {uri: $uri}) RETURN count(c) AS count',
                uri=to_uri
            )
            if result.single()['count'] == 0:
                missing_to.append((r['to']['label'], 'Class'))

print(f"\n=== URI 分析 ===")
print(f"唯一的 from URI (Statement): {len(from_statements)}")
print(f"唯一的 to URI (Concept): {len(to_instances)}")
print(f"唯一的 to URI (Class): {len(to_classes)}")

print(f"\n=== 缺失检查 ===")
print(f"缺失的 Statement: {len(missing_from)}")
if missing_from:
    for s in missing_from[:10]:
        print(f"  - {s}")
print(f"缺失的目标节点: {len(missing_to)}")
if missing_to:
    for label, node_type in missing_to[:10]:
        print(f"  - {label} ({node_type})")

# 查看示例关系
print(f"\n=== 示例关系 (前15个) ===")
for r in relations[:15]:
    to_type = "Class" if "/class/" in r['to']['uri'] else "Concept"
    print(f"  {r['from']['label']} → RELATED_TO → {r['to']['label']} ({to_type})")

client.close()
print("\n✅ 验证完成")