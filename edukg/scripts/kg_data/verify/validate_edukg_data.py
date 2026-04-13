#!/usr/bin/env python3
"""
交叉验证 EDUKG 数学知识图谱数据
对比 TTL 文件解析与 SPARQL 端点查询结果
"""
import os
import json
import re
import requests
from collections import defaultdict
from typing import Dict, List, Set, Tuple

# 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TTL_FILE = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg", "ttl", "math.ttl")
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg", "validation")
SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
GRAPH_IRI = "http://edukg.org/math"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)


def parse_ttl_file(ttl_path: str) -> Dict:
    """
    解析 TTL 文件，提取实体和关系
    返回：
    - entities: 实体列表 (uri, label, types)
    - triples: 三元组数量
    - predicates: 谓词统计
    """
    print(f"[1] 解析 TTL 文件: {ttl_path}")

    entities = {}  # uri -> {"label": str, "types": set}
    predicates = defaultdict(int)
    triple_count = 0

    with open(ttl_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析 prefix
    prefixes = {}
    for line in content.split('\n'):
        if line.startswith('@prefix'):
            match = re.match(r'@prefix\s+(\w+):\s*<([^>]+)>', line)
            if match:
                prefixes[match.group(1)] = match.group(2)

    print(f"  Prefixes: {list(prefixes.keys())}")

    # 解析三元组 - 使用正则表达式
    # 模式: <uri> predicate object ;
    # 或: <uri> predicate object .

    # 简化解析：提取所有完整的三元组行
    lines = content.split('\n')

    current_subject = None
    current_predicates = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('@prefix'):
            continue

        # 新的主体开始
        subject_match = re.match(r'<([^>]+)>\s+(\w+:|\S+)\s+(.+)', line)
        if subject_match:
            uri = subject_match.group(1)
            pred = subject_match.group(2)
            obj_part = subject_match.group(3)

            # 初始化实体
            if uri not in entities:
                entities[uri] = {"label": None, "types": set()}

            # 处理谓词
            pred_name = pred.replace('rdf:type', 'type').replace('rdfs:label', 'label')
            if pred_name in ['rdf:type', 'type']:
                # 提取类型
                types = re.findall(r'ns1:(\S+)', obj_part)
                for t in types:
                    entities[uri]["types"].add(t)
                    predicates['rdf:type'] += 1
                    triple_count += 1
            elif pred_name in ['rdfs:label', 'label']:
                # 提取标签
                label_match = re.search(r'"([^"]+)"', obj_part)
                if label_match:
                    entities[uri]["label"] = label_match.group(1)
                    predicates['rdfs:label'] += 1
                    triple_count += 1

            # 检查是否以 ; 结尾（多谓词）
            if line.endswith(';'):
                current_subject = uri
            else:
                current_subject = None

    # 统计
    print(f"  三元组总数: {triple_count}")
    print(f"  实体总数: {len(entities)}")
    print(f"  谓词分布: {dict(predicates)}")

    # 统计实体类型
    statement_entities = []
    instance_entities = []

    for uri, data in entities.items():
        if 'statement/math#' in uri:
            statement_entities.append(uri)
        elif 'instance/math#' in uri:
            instance_entities.append(uri)

    print(f"  Statement 实体: {len(statement_entities)}")
    print(f"  Instance 实体: {len(instance_entities)}")

    return {
        "entities": entities,
        "triple_count": triple_count,
        "predicates": dict(predicates),
        "statement_count": len(statement_entities),
        "instance_count": len(instance_entities)
    }


def query_sparql_endpoint() -> Dict:
    """
    查询 SPARQL 端点，获取数学图谱统计信息
    """
    print(f"\n[2] 查询 SPARQL 端点: {SPARQL_ENDPOINT}")

    results = {}

    # 2.1 三元组总数
    print("  查询三元组总数...")
    query = f"SELECT (COUNT(*) AS ?count) FROM <{GRAPH_IRI}> WHERE {{ ?s ?p ?o . }}"
    try:
        resp = requests.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"}, timeout=30)
        if resp.status_code == 200:
            count = int(resp.json()["results"]["bindings"][0]["count"]["value"])
            results["triple_count"] = count
            print(f"    三元组总数: {count}")
        else:
            print(f"    查询失败: {resp.status_code}")
            results["triple_count"] = None
    except Exception as e:
        print(f"    错误: {e}")
        results["triple_count"] = None

    # 2.2 实体总数（有标签的）
    print("  查询实体总数...")
    query = f"""
    SELECT (COUNT(DISTINCT ?s) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{
        ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label .
    }}
    """
    try:
        resp = requests.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"}, timeout=30)
        if resp.status_code == 200:
            count = int(resp.json()["results"]["bindings"][0]["count"]["value"])
            results["entity_count"] = count
            print(f"    实体总数: {count}")
        else:
            results["entity_count"] = None
    except Exception as e:
        print(f"    错误: {e}")
        results["entity_count"] = None

    # 2.3 谓词分布
    print("  查询谓词分布...")
    query = f"""
    SELECT ?p (COUNT(*) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{ ?s ?p ?o . }}
    GROUP BY ?p
    ORDER BY DESC(?count)
    """
    try:
        resp = requests.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"}, timeout=30)
        if resp.status_code == 200:
            predicates = {}
            for binding in resp.json()["results"]["bindings"]:
                pred_uri = binding["p"]["value"]
                count = int(binding["count"]["value"])
                # 简化谓词名
                if 'rdf-syntax' in pred_uri:
                    pred_name = 'rdf:type'
                elif 'rdf-schema' in pred_uri:
                    pred_name = 'rdfs:label'
                else:
                    pred_name = pred_uri.split('/')[-1] or pred_uri.split('#')[-1]
                predicates[pred_name] = count
            results["predicates"] = predicates
            print(f"    谓词分布: {predicates}")
        else:
            results["predicates"] = None
    except Exception as e:
        print(f"    错误: {e}")
        results["predicates"] = None

    # 2.4 实体类型统计
    print("  查询实体类型分布...")
    query = f"""
    SELECT (COUNT(?s) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{
        ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label .
        FILTER(STRSTARTS(STR(?s), "http://edukg.org/knowledge/0.1/statement/math#"))
    }}
    """
    try:
        resp = requests.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"}, timeout=30)
        if resp.status_code == 200:
            count = int(resp.json()["results"]["bindings"][0]["count"]["value"])
            results["statement_count"] = count
            print(f"    Statement 实体: {count}")
        else:
            results["statement_count"] = None
    except Exception as e:
        print(f"    错误: {e}")
        results["statement_count"] = None

    query = f"""
    SELECT (COUNT(?s) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{
        ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label .
        FILTER(STRSTARTS(STR(?s), "http://edukg.org/knowledge/0.1/instance/math#"))
    }}
    """
    try:
        resp = requests.get(SPARQL_ENDPOINT, params={"query": query, "format": "json"}, timeout=30)
        if resp.status_code == 200:
            count = int(resp.json()["results"]["bindings"][0]["count"]["value"])
            results["instance_count"] = count
            print(f"    Instance 实体: {count}")
        else:
            results["instance_count"] = None
    except Exception as e:
        print(f"    错误: {e}")
        results["instance_count"] = None

    return results


def compare_results(ttl_data: Dict, sparql_data: Dict) -> Dict:
    """
    交叉验证 TTL 解析和 SPARQL 查询结果
    """
    print("\n[3] 交叉验证结果...")

    comparison = {
        "triple_count": {
            "ttl": ttl_data["triple_count"],
            "sparql": sparql_data.get("triple_count"),
            "match": None,
            "diff": None
        },
        "entity_count": {
            "ttl": len(ttl_data["entities"]),
            "sparql": sparql_data.get("entity_count"),
            "match": None,
            "diff": None
        },
        "statement_count": {
            "ttl": ttl_data["statement_count"],
            "sparql": sparql_data.get("statement_count"),
            "match": None,
            "diff": None
        },
        "instance_count": {
            "ttl": ttl_data["instance_count"],
            "sparql": sparql_data.get("instance_count"),
            "match": None,
            "diff": None
        },
        "predicates": {
            "ttl": ttl_data["predicates"],
            "sparql": sparql_data.get("predicates"),
            "match": None
        }
    }

    # 比较每个指标
    for key in ["triple_count", "entity_count", "statement_count", "instance_count"]:
        ttl_val = comparison[key]["ttl"]
        sparql_val = comparison[key]["sparql"]

        if sparql_val is None:
            comparison[key]["match"] = "SPARQL查询失败"
        elif ttl_val == sparql_val:
            comparison[key]["match"] = "✓ 一致"
            comparison[key]["diff"] = 0
        else:
            comparison[key]["match"] = "✗ 不一致"
            comparison[key]["diff"] = ttl_val - sparql_val

    # 打印比较结果
    print("\n  ========== 验证结果 ==========")
    for key, data in comparison.items():
        if key == "predicates":
            print(f"\n  谓词分布:")
            print(f"    TTL: {data['ttl']}")
            print(f"    SPARQL: {data['sparql']}")
        else:
            print(f"\n  {key}:")
            print(f"    TTL 文件: {data['ttl']}")
            print(f"    SPARQL: {data['sparql']}")
            print(f"    结果: {data['match']}")
            if data['diff']:
                print(f"    差异: {data['diff']}")

    return comparison


def extract_relations(ttl_path: str, output_path: str):
    """
    提取完整关系数据并保存为 JSON
    """
    print(f"\n[4] 提取关系数据...")

    relations = []
    entities = {}

    with open(ttl_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 更精确的三元组解析
    # 匹配模式: <subject> predicate object ;

    pattern = r'<([^>]+)>\s+(\S+)\s+(.+?)(?:[;.]|$)'
    matches = re.findall(pattern, content, re.MULTILINE)

    for subject, predicate, obj in matches:
        # 清理
        predicate = predicate.strip()
        obj = obj.strip().rstrip(';').rstrip('.')

        # 解析谓词
        if predicate.startswith('rdf:type'):
            pred_type = 'rdf:type'
            # 提取类型对象
            type_objs = re.findall(r'ns1:(\S+)', obj)
            for type_obj in type_objs:
                relations.append({
                    "subject": subject,
                    "predicate": pred_type,
                    "object": type_obj,
                    "object_type": "class"
                })
        elif predicate.startswith('rdfs:label'):
            pred_type = 'rdfs:label'
            # 提取标签值
            label_match = re.search(r'"([^"]+)"(?:@(\w+))?', obj)
            if label_match:
                label = label_match.group(1)
                lang = label_match.group(2) or "zh"
                relations.append({
                    "subject": subject,
                    "predicate": pred_type,
                    "object": label,
                    "object_type": "literal",
                    "language": lang
                })
                # 记录实体标签
                if subject not in entities:
                    entities[subject] = {"uri": subject}
                entities[subject]["label"] = label

    # 保存关系数据
    output_data = {
        "metadata": {
            "source": ttl_path,
            "total_relations": len(relations),
            "unique_entities": len(entities)
        },
        "relations": relations[:1000],  # 只保存前1000条作为示例
        "entities": list(entities.values())[:500]  # 只保存前500个实体作为示例
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"  总关系数: {len(relations)}")
    print(f"  唯一实体数: {len(entities)}")
    print(f"  已保存示例数据: {output_path}")

    return relations, entities


def main():
    print("=" * 70)
    print("EDUKG 数学知识图谱 - TTL 与 SPARQL 交叉验证")
    print("=" * 70)

    # 1. 解析 TTL 文件
    ttl_data = parse_ttl_file(TTL_FILE)

    # 2. 查询 SPARQL 端点
    sparql_data = query_sparql_endpoint()

    # 3. 交叉验证
    comparison = compare_results(ttl_data, sparql_data)

    # 4. 提取关系数据
    relations_output = os.path.join(OUTPUT_DIR, "math_relations.json")
    relations, entities = extract_relations(TTL_FILE, relations_output)

    # 5. 保存验证报告
    report = {
        "timestamp": "2026-03-31",
        "ttl_file": TTL_FILE,
        "sparql_endpoint": SPARQL_ENDPOINT,
        "graph_iri": GRAPH_IRI,
        "ttl_stats": {
            "triple_count": ttl_data["triple_count"],
            "entity_count": len(ttl_data["entities"]),
            "statement_count": ttl_data["statement_count"],
            "instance_count": ttl_data["instance_count"],
            "predicates": ttl_data["predicates"]
        },
        "sparql_stats": sparql_data,
        "comparison": comparison,
        "conclusion": "数据一致性验证完成"
    }

    report_path = os.path.join(OUTPUT_DIR, "validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n验证报告已保存: {report_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()