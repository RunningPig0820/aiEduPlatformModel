#!/usr/bin/env python3
"""
分析教材知识点与 Concept 的匹配情况
"""
import json
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

# 连接 Neo4j
client = Neo4jClient()

# 获取所有 Concept 的 label
with client.session() as session:
    result = session.run("MATCH (c:Concept) RETURN c.label AS label")
    concept_labels = set(row["label"] for row in result)

print(f"现有 Concept 数量: {len(concept_labels)}")

# 读取教材数据
textbook_dir = os.path.join(PROJECT_ROOT, "edukg/data/textbook/math/renjiao")

# 收集所有教材知识点
all_textbook_kps = set()
exclude_kps = {"数学活动", "小结", "构建知识体系", "习题训练", "章前引言", "测试",
               "部分中英文词汇索引", "构建知识体系和应用"}

for stage in ["primary", "middle", "high"]:
    stage_dir = os.path.join(textbook_dir, stage)
    if not os.path.exists(stage_dir):
        continue

    for root, dirs, files in os.walk(stage_dir):
        for f in files:
            if f.endswith(".json") and "textbook" not in f:
                filepath = os.path.join(root, f)
                with open(filepath, "r", encoding="utf-8") as fp:
                    data = json.load(fp)

                    for chapter in data.get("chapters", []):
                        for section in chapter.get("sections", []):
                            for kp in section.get("knowledge_points", []):
                                if kp not in exclude_kps and not kp.startswith("复习题"):
                                    all_textbook_kps.add(kp)

print(f"教材知识点数量: {len(all_textbook_kps)}")

# 匹配分析
matched = []
unmatched = []

for kp in all_textbook_kps:
    if kp in concept_labels:
        matched.append(kp)
    else:
        unmatched.append(kp)

print(f"\n=== 匹配结果 ===")
print(f"匹配成功: {len(matched)} ({len(matched)*100//len(all_textbook_kps)}%)")
print(f"匹配失败: {len(unmatched)} ({len(unmatched)*100//len(all_textbook_kps)}%)")

print(f"\n匹配成功示例 (前20个):")
for kp in sorted(matched)[:20]:
    print(f"  ✓ {kp}")

print(f"\n匹配失败示例 (前30个):")
for kp in sorted(unmatched)[:30]:
    print(f"  ✗ {kp}")

# 保存匹配结果
result = {
    "stats": {
        "total_textbook_kps": len(all_textbook_kps),
        "total_concepts": len(concept_labels),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "match_rate": f"{len(matched)*100//len(all_textbook_kps)}%"
    },
    "matched": sorted(matched),
    "unmatched": sorted(unmatched)
}

output_file = os.path.join(textbook_dir, "kp_matching_result.json")
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"\n匹配结果已保存: {output_file}")

client.close()