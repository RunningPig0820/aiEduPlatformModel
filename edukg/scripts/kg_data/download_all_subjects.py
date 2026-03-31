#!/usr/bin/env python3
"""
EDUKG 知识图谱 - 完整数据下载脚本（支持所有学科）
分批下载所有谓词类型的三元组，确保数据完整

使用方法：
    # 下载所有学科
    python download_all_subjects.py

    # 下载指定学科
    python download_all_subjects.py --subject math
    python download_all_subjects.py --subject math,physics,chemistry

    # 查看学科统计信息
    python download_all_subjects.py --stats
"""
import os
import json
import requests
import argparse
from tqdm import tqdm
from typing import Dict, List, Optional
import time

# 配置
SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg", "complete")

# 所有学科图谱
SUBJECTS = {
    "math": "数学",
    "physics": "物理",
    "chemistry": "化学",
    "biology": "生物",
    "chinese": "语文",
    "english": "英语",
    "history": "历史",
    "geo": "地理",
    "politics": "政治",
}

# EDUKG 常用谓词（完整 URI）
COMMON_PREDICATES = {
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


def query_sparql(query: str, format: str = "json", timeout: int = 120) -> Dict:
    """执行 SPARQL 查询"""
    headers = {"Accept": f"application/sparql-results+{format}"}
    params = {"query": query, "format": format}

    max_retries = 3
    for i in range(max_retries):
        try:
            response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=timeout)
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


def get_graph_stats(graph_iri: str) -> Dict:
    """获取图谱统计信息"""
    stats = {"graph": graph_iri}

    # 三元组总数
    query = f"SELECT (COUNT(*) AS ?count) FROM <{graph_iri}> WHERE {{ ?s ?p ?o . }}"
    result = query_sparql(query)
    stats["triple_count"] = int(result["results"]["bindings"][0]["count"]["value"])

    # 实体总数
    query = f"""
    SELECT (COUNT(DISTINCT ?s) AS ?count)
    FROM <{graph_iri}>
    WHERE {{ ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label . }}
    """
    result = query_sparql(query)
    stats["entity_count"] = int(result["results"]["bindings"][0]["count"]["value"])

    # 谓词分布
    query = f"""
    SELECT ?p (COUNT(*) AS ?count)
    FROM <{graph_iri}>
    WHERE {{ ?s ?p ?o . }}
    GROUP BY ?p
    ORDER BY DESC(?count)
    """
    result = query_sparql(query)
    predicates = {}
    for binding in result["results"]["bindings"]:
        pred_uri = binding["p"]["value"]
        count = int(binding["count"]["value"])
        pred_name = pred_uri.split('#')[-1]
        predicates[pred_name] = count
    stats["predicates"] = predicates

    return stats


def show_all_stats():
    """显示所有学科的统计信息"""
    print("=" * 80)
    print("EDUKG 所有学科知识图谱统计")
    print("=" * 80)

    all_stats = []
    total_triples = 0
    total_entities = 0

    for subject, name in tqdm(SUBJECTS.items(), desc="查询统计"):
        graph_iri = f"http://edukg.org/{subject}"
        try:
            stats = get_graph_stats(graph_iri)
            stats["subject"] = subject
            stats["name"] = name
            all_stats.append(stats)
            total_triples += stats["triple_count"]
            total_entities += stats["entity_count"]
        except Exception as e:
            print(f"  {subject} 查询失败: {e}")
            all_stats.append({
                "subject": subject,
                "name": name,
                "triple_count": 0,
                "entity_count": 0,
                "error": str(e)
            })

    # 打印统计表
    print(f"\n{'学科':<12} {'名称':<10} {'三元组':>10} {'实体':>10} {'relatedTo':>10}")
    print("-" * 80)

    for stats in all_stats:
        related_count = stats.get("predicates", {}).get("relatedTo", 0)
        print(f"{stats['subject']:<12} {stats['name']:<10} {stats.get('triple_count', 0):>10,} {stats.get('entity_count', 0):>10,} {related_count:>10,}")

    print("-" * 80)
    print(f"{'总计':<12} {'':<10} {total_triples:>10,} {total_entities:>10,}")
    print("=" * 80)

    # 保存统计报告
    report = {
        "query_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_triples": total_triples,
        "total_entities": total_entities,
        "subjects": all_stats
    }

    report_file = os.path.join(OUTPUT_DIR, "all_subjects_stats.json")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n统计报告已保存: complete/all_subjects_stats.json")

    return all_stats


def download_predicate_triples(graph_iri: str, predicate_uri: str, predicate_name: str, batch_size: int = 5000) -> List[Dict]:
    """分批下载指定谓词的所有三元组"""
    triples = []

    # 获取总数
    count_query = f"""
    SELECT (COUNT(*) AS ?count)
    FROM <{graph_iri}>
    WHERE {{ ?s <{predicate_uri}> ?o . }}
    """
    result = query_sparql(count_query)
    total = int(result["results"]["bindings"][0]["count"]["value"])

    if total == 0:
        return triples

    # 分批下载
    batches = (total // batch_size) + 1

    for batch in range(batches):
        offset = batch * batch_size

        query = f"""
        SELECT ?s ?o
        FROM <{graph_iri}>
        WHERE {{ ?s <{predicate_uri}> ?o . }}
        OFFSET {offset}
        LIMIT {batch_size}
        """

        try:
            result = query_sparql(query)
            bindings = result["results"]["bindings"]

            for binding in bindings:
                triples.append({
                    "subject": binding["s"]["value"],
                    "predicate": predicate_name,
                    "predicate_uri": predicate_uri,
                    "object": binding["o"]["value"],
                    "object_type": binding["o"].get("type", "uri")
                })

            if len(bindings) < batch_size:
                break

        except Exception as e:
            print(f"  批次 {batch} 错误: {e}")
            break

    return triples


def download_subject_data(subject: str, name: str) -> Dict:
    """下载单个学科的完整数据"""
    graph_iri = f"http://edukg.org/{subject}"
    subject_dir = os.path.join(OUTPUT_DIR, subject)
    os.makedirs(subject_dir, exist_ok=True)

    # 使用相对路径
    relative_dir = f"complete/{subject}"

    print(f"\n{'='*70}")
    print(f"下载学科: {name} ({subject})")
    print(f"图谱 URI: {graph_iri}")
    print(f"{'='*70}")

    # 1. 先查询谓词列表（动态获取）
    query = f"""
    SELECT DISTINCT ?p (COUNT(*) AS ?count)
    FROM <{graph_iri}>
    WHERE {{ ?s ?p ?o . }}
    GROUP BY ?p
    ORDER BY DESC(?count)
    """
    result = query_sparql(query)
    predicates = {}
    for binding in result["results"]["bindings"]:
        pred_uri = binding["p"]["value"]
        count = int(binding["count"]["value"])
        pred_name = pred_uri.split('#')[-1]
        predicates[pred_name] = pred_uri

    print(f"\n发现谓词: {list(predicates.keys())}")

    # 2. 下载实体列表
    print("\n下载实体列表...")
    query = f"""
    SELECT ?s ?label ?type
    FROM <{graph_iri}>
    WHERE {{
        ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label .
        OPTIONAL {{ ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type . }}
    }}
    """
    result = query_sparql(query, timeout=180)
    bindings = result["results"]["bindings"]

    entities = {}
    for binding in bindings:
        uri = binding["s"]["value"]
        label = binding["label"]["value"]
        type_uri = binding.get("type", {}).get("value")

        if uri not in entities:
            entities[uri] = {"uri": uri, "label": label, "types": []}

        if type_uri:
            type_name = type_uri.split('#')[-1] or type_uri.split('/')[-1]
            entities[uri]["types"].append(type_name)

    entity_list = list(entities.values())
    print(f"  实体总数: {len(entity_list)}")

    # 保存实体（使用相对路径）
    entities_file = os.path.join(subject_dir, f"{subject}_entities_complete.json")
    entities_file_relative = f"{relative_dir}/{subject}_entities_complete.json"
    with open(entities_file, "w", encoding="utf-8") as f:
        json.dump(entity_list, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {entities_file_relative}")

    # 3. 按谓词下载三元组
    print("\n下载三元组...")
    all_triples = []
    predicate_stats = {}

    for pred_name, pred_uri in tqdm(predicates.items(), desc="谓词"):
        triples = download_predicate_triples(graph_iri, pred_uri, pred_name)
        if triples:
            all_triples.extend(triples)
            predicate_stats[pred_name] = len(triples)

    print(f"\n谓词统计:")
    for pred, count in predicate_stats.items():
        print(f"  {pred}: {count}")
    print(f"\n总三元组: {len(all_triples)}")

    # 保存完整关系数据（使用相对路径）
    relations_file_relative = f"{relative_dir}/{subject}_relations_complete.json"
    all_data = {
        "metadata": {
            "subject": subject,
            "name": name,
            "graph": graph_iri,
            "download_time": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "predicate_stats": predicate_stats,
        "relations": all_triples
    }
    with open(relations_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {relations_file_relative}")

    # 4. 生成知识点关联关系（简化版）
    related_relations = []
    for triple in all_triples:
        if triple["predicate"] == "relatedTo":
            subject_uri = triple["subject"]
            object_uri = triple["object"]

            subject_label = next((e["label"] for e in entity_list if e["uri"] == subject_uri), None)
            object_label = next((e["label"] for e in entity_list if e["uri"] == object_uri), None)

            related_relations.append({
                "from": {"uri": subject_uri, "label": subject_label},
                "relation": "relatedTo",
                "to": {"uri": object_uri, "label": object_label}
            })

    # 保存知识点关联（使用相对路径）
    relations_simple_file_relative = f"{relative_dir}/{subject}_knowledge_relations.json"
    with open(relations_simple_file, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "total_relations": len(related_relations),
                "description": f"{name}知识点关联关系"
            },
            "relations": related_relations
        }, f, ensure_ascii=False, indent=2)
    print(f"  已保存: {relations_simple_file_relative} ({len(related_relations)} 条关联)")

    # 5. 下载报告（使用相对路径）
    report = {
        "subject": subject,
        "name": name,
        "download_time": all_data["metadata"]["download_time"],
        "entity_count": len(entity_list),
        "total_triples": len(all_triples),
        "predicate_stats": predicate_stats,
        "output_files": {
            "entities": entities_file_relative,
            "relations_complete": relations_file_relative,
            "relations_simple": relations_simple_file_relative
        }
    }

    report_file = os.path.join(subject_dir, "download_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {relative_dir}/download_report.json")

    return report


def main():
    parser = argparse.ArgumentParser(description="EDUKG 知识图谱完整数据下载工具")
    parser.add_argument("--stats", action="store_true", help="只显示统计信息，不下载")
    parser.add_argument("--subject", type=str, help="指定学科，如 'math' 或 'math,physics'")
    parser.add_argument("--all", action="store_true", help="下载所有学科")

    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.stats:
        show_all_stats()
        return

    if args.all:
        subjects_to_download = list(SUBJECTS.keys())
    elif args.subject:
        subjects_to_download = [s.strip() for s in args.subject.split(",")]
    else:
        # 默认下载所有
        subjects_to_download = list(SUBJECTS.keys())

    # 验证学科名
    for s in subjects_to_download:
        if s not in SUBJECTS:
            print(f"错误: 未知学科 '{s}'")
            print(f"支持的学科: {list(SUBJECTS.keys())}")
            return

    print("=" * 80)
    print("EDUKG 知识图谱 - 完整数据下载")
    print("=" * 80)
    print(f"将下载学科: {subjects_to_download}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 先显示统计
    print("\n先查询各学科统计信息...")
    stats = show_all_stats()

    # 下载每个学科
    all_reports = []
    for subject in subjects_to_download:
        name = SUBJECTS[subject]
        try:
            report = download_subject_data(subject, name)
            all_reports.append(report)
        except Exception as e:
            print(f"\n错误: {subject} 下载失败: {e}")
            all_reports.append({"subject": subject, "error": str(e)})

    # 总结报告
    summary = {
        "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_subjects": len(subjects_to_download),
        "successful": len([r for r in all_reports if "error" not in r]),
        "failed": len([r for r in all_reports if "error" in r]),
        "subjects": all_reports
    }

    summary_file = os.path.join(OUTPUT_DIR, "download_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("下载完成！")
    print(f"成功: {summary['successful']} / 失败: {summary['failed']}")
    print(f"总结报告: complete/download_summary.json")
    print("=" * 80)


if __name__ == "__main__":
    main()