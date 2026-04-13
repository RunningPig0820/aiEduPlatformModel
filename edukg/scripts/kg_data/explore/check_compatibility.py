#!/usr/bin/env python3
"""
对比 edukg.org 和 edukb.org 的数据兼容性
"""
import os
import re

def extract_entities(ttl_file, source_name):
    """提取 TTL 文件中的实体"""
    entities = {}
    with open(ttl_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 URI 和标签
    # 格式: <URI> rdfs:label "标签"
    pattern = r'<(http://[^>]+)>\s*rdfs:label\s*"([^"]+)"'
    matches = re.findall(pattern, content)

    for uri, label in matches:
        if len(label) >= 2 and not label.startswith('http'):
            entities[label] = uri

    return entities

# 数据目录 (相对路径)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg")

# 检查数学数据
edukg_entities = extract_entities(os.path.join(DATA_DIR, 'ttl', 'math.ttl'), 'edukg')
edukb_entities = extract_entities(os.path.join(DATA_DIR, 'relations', 'math_relations.ttl'), 'edukb')

print("=" * 70)
print("EDUKG vs EDUKB 数据兼容性分析")
print("=" * 70)

print(f"\nedukg.org 实体数: {len(edukg_entities)}")
print(f"edukb.org 实体数: {len(edukb_entities)}")

# 找出相同标签的实体
common_labels = set(edukg_entities.keys()) & set(edukb_entities.keys())
print(f"\n相同标签的实体数: {len(common_labels)}")

if common_labels:
    print("\n示例 - 相同标签，不同 URI:")
    for label in list(common_labels)[:5]:
        print(f"\n  标签: {label}")
        print(f"    edukg URI: {edukg_entities[label]}")
        print(f"    edukb URI: {edukb_entities[label]}")

# 检查 URI 格式差异
print("\n" + "=" * 70)
print("URI 格式对比")
print("=" * 70)

edukg_sample = list(edukg_entities.items())[:3]
edukb_sample = list(edukb_entities.items())[:3]

print("\nedukg.org URI 格式示例:")
for label, uri in edukg_sample:
    print(f"  {label}: {uri}")

print("\nedukb.org URI 格式示例:")
for label, uri in edukb_sample:
    print(f"  {label}: {uri}")

# 结论
print("\n" + "=" * 70)
print("兼容性结论")
print("=" * 70)

if len(common_labels) > 0:
    print(f"""
⚠️ 部分兼容

- 两个数据源有 {len(common_labels)} 个相同标签的知识点
- 但 URI 完全不同，无法直接关联
- 需要通过标签进行匹配/映射
""")
else:
    print("""
❌ 不兼容

- 两个数据源使用完全不同的 URI 命名空间
- 没有共同标识符
""")