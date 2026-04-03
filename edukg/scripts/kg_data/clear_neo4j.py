#!/usr/bin/env python3
"""
清空 Neo4j 数据库
"""
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

os.chdir(AI_SERVICE_DIR)

from edukg.core.neo4j.client import Neo4jClient
from config.settings import settings

client = Neo4jClient()

print("清空 Neo4j 数据...")

with client.session() as session:
    # 删除所有关系
    session.run("MATCH ()-[r]->() DELETE r")
    result = session.run("MATCH (n) DELETE n RETURN count(n) as deleted")
    deleted = result.single()["deleted"]
    print(f"已删除 {deleted} 个节点")

# 验证
with client.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    count = result.single()["count"]
    print(f"当前节点数: {count}")

client.close()
print("✅ 数据清空完成")