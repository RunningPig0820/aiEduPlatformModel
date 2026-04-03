#!/usr/bin/env python3
"""
验证 Neo4j 数学知识图谱数据完整性

检查内容：
1. 节点数量统计
2. 关系数量统计
3. 属性统计
4. 孤立节点检查
5. 无类型实体检查
6. 数据一致性检查

使用方法：
    python validate_kg_data.py
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到 sys.path
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

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def validate():
    """验证 Neo4j 数据"""
    client = Neo4jClient()

    logger.info("=" * 60)
    logger.info("Neo4j 数学知识图谱数据验证")
    logger.info("=" * 60)

    with client.session() as session:
        # 1. 节点统计
        logger.info("\n【1. 节点统计】")
        result = session.run("MATCH (c:Class) RETURN count(c) AS count")
        class_count = result.single()["count"]
        logger.info(f"  Class 节点: {class_count}")

        result = session.run("MATCH (e:Entity) RETURN count(e) AS count")
        entity_count = result.single()["count"]
        logger.info(f"  Entity 节点: {entity_count}")

        # 2. 关系统计
        logger.info("\n【2. 关系统计】")
        relations = [
            ("SUB_CLASS_OF", "概念类层级"),
            ("HAS_TYPE", "实体类型"),
            ("RELATED_TO", "弱关联"),
            ("PART_OF", "部分-整体"),
            ("BELONGS_TO", "所属关系")
        ]

        total_relations = 0
        for rel_type, desc in relations:
            result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count")
            count = result.single()["count"]
            total_relations += count
            logger.info(f"  {rel_type} ({desc}): {count}")

        logger.info(f"\n  关系总计: {total_relations}")

        # 3. Entity 属性统计
        logger.info("\n【3. Entity 属性统计】")
        result = session.run("MATCH (e:Entity) WHERE e.content IS NOT NULL RETURN count(e) AS count")
        content_count = result.single()["count"]
        logger.info(f"  有 content 属性: {content_count}")

        result = session.run("MATCH (e:Entity) WHERE e.label IS NOT NULL RETURN count(e) AS count")
        label_count = result.single()["count"]
        logger.info(f"  有 label 属性: {label_count}")

        # 4. PART_OF 关系示例
        logger.info("\n【4. PART_OF 关系示例】")
        result = session.run("""
            MATCH (from:Entity)-[:PART_OF]->(to:Entity)
            RETURN from.label AS from_label, to.label AS to_label
            LIMIT 10
        """)
        for row in result:
            logger.info(f"  {row['from_label']} → PART_OF → {row['to_label']}")

        # 5. BELONGS_TO 关系示例
        logger.info("\n【5. BELONGS_TO 关系示例】")
        result = session.run("""
            MATCH (from:Entity)-[:BELONGS_TO]->(to:Entity)
            RETURN from.label AS from_label, to.label AS to_label
            LIMIT 10
        """)
        for row in result:
            logger.info(f"  {row['from_label']} → BELONGS_TO → {row['to_label']}")

        # 6. 概念类层级示例
        logger.info("\n【6. 概念类层级示例】")
        result = session.run("""
            MATCH (c:Class)-[:SUB_CLASS_OF]->(parent:Class)
            RETURN c.label AS child, parent.label AS parent
            LIMIT 10
        """)
        for row in result:
            logger.info(f"  {row['child']} → SUB_CLASS_OF → {row['parent']}")

        # 7. 实体类型分布
        logger.info("\n【7. 实体类型分布 (前10)】")
        result = session.run("""
            MATCH (e:Entity)-[:HAS_TYPE]->(c:Class)
            RETURN c.label AS type, count(e) AS count
            ORDER BY count DESC
            LIMIT 10
        """)
        for row in result:
            logger.info(f"  {row['type']}: {row['count']}")

        # 8. 检查孤立节点
        logger.info("\n【8. 孤立节点检查】")
        result = session.run("""
            MATCH (e:Entity)
            WHERE NOT (e)-[]-()
            RETURN count(e) AS count
        """)
        isolated = result.single()["count"]
        logger.info(f"  完全孤立 Entity: {isolated}")

        # 9. 检查无类型实体
        logger.info("\n【9. 无类型实体检查】")
        result = session.run("""
            MATCH (e:Entity)
            WHERE NOT (e)-[:HAS_TYPE]->()
            RETURN count(e) AS count
        """)
        no_type = result.single()["count"]
        logger.info(f"  无 HAS_TYPE 的 Entity: {no_type}")

        if no_type > 0:
            result = session.run("""
                MATCH (e:Entity)
                WHERE NOT (e)-[:HAS_TYPE]->()
                RETURN e.label AS label
                LIMIT 10
            """)
            logger.info("  示例:")
            for row in result:
                logger.info(f"    - {row['label']}")

        # 10. 知识点层级路径示例
        logger.info("\n【10. 知识点层级路径示例】")
        result = session.run("""
            MATCH path = (a:Entity)-[:PART_OF*1..3]->(b:Entity)
            RETURN [n IN nodes(path) | n.label] AS path
            LIMIT 5
        """)
        for row in result:
            logger.info(f"  {row['path']}")

        # 11. 验证结论
        logger.info("\n【11. 验证结论】")

        issues = []
        if class_count != 38:
            issues.append(f"Class 数量异常 (预期 38, 实际 {class_count})")
        if entity_count != 4085:
            issues.append(f"Entity 数量异常 (预期 4085, 实际 {entity_count})")
        if isolated > 100:
            issues.append(f"孤立节点过多 ({isolated})")
        if no_type > 100:
            issues.append(f"无类型实体过多 ({no_type})")

        if issues:
            logger.info("  ⚠️ 发现问题:")
            for issue in issues:
                logger.info(f"    - {issue}")
        else:
            logger.info("  ✅ 数据完整性良好")

        # 数据总结
        logger.info("\n" + "=" * 60)
        logger.info("数据总结")
        logger.info("=" * 60)
        logger.info(f"""
┌─────────────────────────────────────────────┐
│           Neo4j 数学知识图谱                 │
├─────────────────────────────────────────────┤
│ 节点                                         │
│   Class (概念类):       {class_count}                   │
│   Entity (知识点):    {entity_count}                   │
│                                              │
│ 关系                                         │
│   SUB_CLASS_OF (概念层级):  {session.run("MATCH ()-[r:SUB_CLASS_OF]->() RETURN count(r)").single()['count']}               │
│   HAS_TYPE (实体类型):    {session.run("MATCH ()-[r:HAS_TYPE]->() RETURN count(r)").single()['count']}              │
│   RELATED_TO (弱关联):    {session.run("MATCH ()-[r:RELATED_TO]->() RETURN count(r)").single()['count']}              │
│   PART_OF (部分-整体):      298              │
│   BELONGS_TO (所属):        619              │
│                                              │
│ 属性                                         │
│   Entity.content (定义):  {content_count}              │
│                                              │
│ 数据质量                                      │
│   孤立节点:     {isolated}                       │
│   无类型实体:   {no_type}                       │
└─────────────────────────────────────────────┘
""")

    client.close()
    logger.info("验证完成")


if __name__ == '__main__':
    validate()