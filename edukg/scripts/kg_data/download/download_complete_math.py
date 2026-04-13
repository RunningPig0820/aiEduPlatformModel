#!/usr/bin/env python3
"""
EDUKG 数学知识图谱 - 完整数据下载脚本
分批下载所有谓词类型的三元组，确保数据完整
"""
import os
import json
import requests
from tqdm import tqdm
from typing import Dict, List
import time

# 配置
SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
GRAPH_IRI = "http://edukg.org/math"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "edukg", "complete")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# EDUKG 常用谓词（完整 URI）
PREDICATES = {
    "relatedTo": "http://edukg.org/knowledge/0.1/property/common#relatedTo",
    "rdf_type": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "rdfs_label": "http://www.w3.org/2000/01/rdf-schema#label",
    "topicOf": "http://edukg.org/knowledge/0.1/property/common#topicOf",
    "content": "http://edukg.org/knowledge/0.1/property/common#content",
    "page": "http://edukg.org/knowledge/0.1/property/common#page",
    "source": "http://edukg.org/knowledge/0.1/property/common#source",
    "category": "http://edukg.org/knowledge/0.1/property/common#category",
    "belongsTo": "http://edukg.org/knowledge/0.1/property/common#belongsTo",
    "partOf": "http://edukg.org/knowledge/0.1/property/common#partOf",
    "leftRelate": "http://edukg.org/knowledge/0.1/property/common#leftRelate",
    "rightRelate": "http://edukg.org/knowledge/0.1/property/common#rightRelate",
}


def query_sparql(query: str, format: str = "json") -> Dict:
    """执行 SPARQL 查询"""
    headers = {"Accept": f"application/sparql-results+{format}"}
    params = {"query": query, "format": format}

    max_retries = 3
    for i in range(max_retries):
        try:
            response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"  超时，重试 {i+1}/{max_retries}...")
            time.sleep(5)
        except Exception as e:
            print(f"  错误: {e}")
            if i < max_retries - 1:
                time.sleep(5)
            else:
                raise


def download_predicate_triples(predicate_uri: str, predicate_name: str, batch_size: int = 5000) -> List[Dict]:
    """
    分批下载指定谓词的所有三元组
    """
    print(f"\n 下载谓词: {predicate_name}")

    triples = []
    offset = 0

    # 先获取总数
    count_query = f"""
    SELECT (COUNT(*) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{
        ?s <{predicate_uri}> ?o .
    }}
    """
    result = query_sparql(count_query)
    total = int(result["results"]["bindings"][0]["count"]["value"])
    print(f"   总数: {total}")

    if total == 0:
        return triples

    # 分批下载
    batches = (total // batch_size) + 1

    for batch in tqdm(range(batches), desc=f"   {predicate_name}", leave=False):
        offset = batch * batch_size

        query = f"""
        SELECT ?s ?o
        FROM <{GRAPH_IRI}>
        WHERE {{
            ?s <{predicate_uri}> ?o .
        }}
        OFFSET {offset}
        LIMIT {batch_size}
        """

        try:
            result = query_sparql(query)
            bindings = result["results"]["bindings"]

            for binding in bindings:
                subject = binding["s"]["value"]
                object_val = binding["o"]["value"]
                object_type = binding["o"].get("type", "uri")

                triples.append({
                    "subject": subject,
                    "predicate": predicate_name,
                    "predicate_uri": predicate_uri,
                    "object": object_val,
                    "object_type": object_type  # uri, literal, typed-literal
                })

            if len(bindings) < batch_size:
                break  # 已下载完

        except Exception as e:
            print(f"   批次 {batch} 错误: {e}")
            break

    print(f"   下载: {len(triples)} 条")
    return triples


def download_all_entities_with_labels() -> List[Dict]:
    """
    下载所有实体及其标签和类型
    """
    print("\n 下载实体列表（含标签和类型）")

    query = f"""
    SELECT ?s ?label ?type
    FROM <{GRAPH_IRI}>
    WHERE {{
        ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label .
        OPTIONAL {{ ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type . }}
    }}
    ORDER BY ?s
    """

    result = query_sparql(query)
    bindings = result["results"]["bindings"]

    # 按实体聚合
    entities = {}
    for binding in bindings:
        uri = binding["s"]["value"]
        label = binding["label"]["value"]
        type_uri = binding.get("type", {}).get("value")

        if uri not in entities:
            entities[uri] = {"uri": uri, "label": label, "types": []}

        if type_uri:
            # 简化类型名
            type_name = type_uri.split('#')[-1] or type_uri.split('/')[-1]
            entities[uri]["types"].append(type_name)

    entity_list = list(entities.values())
    print(f"   实体总数: {len(entity_list)}")

    return entity_list


def download_complete_relations() -> Dict:
    """
    下载完整的关系数据
    """
    print("=" * 70)
    print("EDUKG 数学知识图谱 - 完整数据下载")
    print("=" * 70)

    all_data = {
        "metadata": {
            "graph": GRAPH_IRI,
            "endpoint": SPARQL_ENDPOINT,
            "download_time": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "entities": [],
        "relations": {}
    }

    # 1. 下载实体列表
    entities = download_all_entities_with_labels()
    all_data["entities"] = entities

    # 保存实体数据
    entities_file = os.path.join(OUTPUT_DIR, "math_entities_complete.json")
    with open(entities_file, "w", encoding="utf-8") as f:
        json.dump(entities, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {entities_file}")

    # 2. 按谓词下载关系
    print("\n 按谓词下载三元组...")

    relation_stats = {}
    all_triples = []

    for pred_name, pred_uri in tqdm(PREDICATES.items(), desc="谓词"):
        triples = download_predicate_triples(pred_uri, pred_name)
        if triples:
            all_data["relations"][pred_name] = triples
            all_triples.extend(triples)
            relation_stats[pred_name] = len(triples)

    print(f"\n 关系统计:")
    for pred, count in relation_stats.items():
        print(f"   {pred}: {count}")

    print(f"\n 总三元组: {len(all_triples)}")

    # 保存完整关系数据
    relations_file = os.path.join(OUTPUT_DIR, "math_relations_complete.json")
    with open(relations_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {relations_file}")

    # 3. 生成简化版关系数据（用于图谱构建）
    print("\n 生成简化版关系数据...")

    simplified_relations = []
    for triple in all_triples:
        # 只保留知识点之间的关联关系
        if triple["predicate"] == "relatedTo":
            subject_uri = triple["subject"]
            object_uri = triple["object"]

            # 查找标签
            subject_label = next((e["label"] for e in entities if e["uri"] == subject_uri), None)
            object_label = next((e["label"] for e in entities if e["uri"] == object_uri), None)

            simplified_relations.append({
                "from": {
                    "uri": subject_uri,
                    "label": subject_label
                },
                "relation": "relatedTo",
                "to": {
                    "uri": object_uri,
                    "label": object_label
                }
            })

    # 保存知识点关联关系
    relations_simple_file = os.path.join(OUTPUT_DIR, "math_knowledge_relations.json")
    with open(relations_simple_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "total_relations": len(simplified_relations),
                "description": "知识点之间的关联关系（relatedTo）"
            },
            "relations": simplified_relations
        }, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {relations_simple_file} ({len(simplified_relations)} 条知识点关联)")

    # 4. 生成统计报告
    report = {
        "download_time": all_data["metadata"]["download_time"],
        "entity_count": len(entities),
        "total_triples": len(all_triples),
        "predicate_stats": relation_stats,
        "output_files": {
            "entities": entities_file,
            "relations_complete": relations_file,
            "relations_simple": relations_simple_file
        }
    }

    report_file = os.path.join(OUTPUT_DIR, "download_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n 报告已保存: {report_file}")

    print("=" * 70)
    print("下载完成！")
    print("=" * 70)

    return all_data


if __name__ == "__main__":
    download_complete_relations()