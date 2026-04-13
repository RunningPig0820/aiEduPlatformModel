#!/usr/bin/env python3
"""
按学科下载 EDUKG 的 Category 和 Class 数据
用于构建学科知识图谱的元数据层
"""
import os
import json
import requests
from tqdm import tqdm
from typing import Dict, List
import time

# 配置
SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg", "meta")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 学科列表
SUBJECTS = ["math", "physics", "chemistry", "biology", "chinese", "history", "geo", "politics", "english"]

# 学科中文名
SUBJECT_NAMES = {
    "math": "数学",
    "physics": "物理",
    "chemistry": "化学",
    "biology": "生物",
    "chinese": "语文",
    "history": "历史",
    "geo": "地理",
    "politics": "政治",
    "english": "英语"
}


def query_sparql(query: str, format: str = "json") -> Dict:
    """执行 SPARQL 查询"""
    headers = {"Accept": f"application/sparql-results+{format}"}
    params = {"query": query, "format": format}

    max_retries = 3
    for i in range(max_retries):
        try:
            response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"  超时，重试 {i+1}/{max_retries}...")
            time.sleep(2)
        except Exception as e:
            if i < max_retries - 1:
                time.sleep(2)
            else:
                raise


def download_subject_categories(subject: str) -> List[Dict]:
    """
    下载学科的 category 数据（教材目录/章节）
    注意：只有数学学科有这个数据结构
    """
    graph_iri = f"http://edukb.org/{subject}"
    category_type = f"http://edukb.org/knowledge/0.1/class/{subject}#1"

    query = f"""
    SELECT ?s ?label
    FROM <{graph_iri}>
    WHERE {{
        ?s rdf:type <{category_type}> .
        ?s rdfs:label ?label .
    }}
    """

    try:
        result = query_sparql(query)
        categories = []

        for binding in result["results"]["bindings"]:
            uri = binding["s"]["value"]
            label = binding["label"]["value"]
            # 提取 ID
            id_part = uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

            categories.append({
                "uri": uri,
                "id": id_part,
                "label": label,
                "type": "category"
            })

        return categories
    except Exception as e:
        print(f"  下载 {subject} category 失败: {e}")
        return []


def download_subject_classes(subject: str) -> List[Dict]:
    """
    下载学科的 class 数据（知识点类型）
    如：定理、法则、概念等
    """
    graph_iri = f"http://edukb.org/{subject}"

    # 查询 owl:Class 及其标签和描述
    query = f"""
    SELECT ?s ?label ?description ?parent
    FROM <{graph_iri}>
    WHERE {{
        ?s rdf:type owl:Class .
        OPTIONAL {{ ?s rdfs:label ?label . }}
        OPTIONAL {{ ?s dc:description ?description . }}
        OPTIONAL {{ ?s rdfs:subClassOf ?parent . }}
    }}
    """

    try:
        result = query_sparql(query)
        classes = {}

        for binding in result["results"]["bindings"]:
            uri = binding["s"]["value"]
            label = binding.get("label", {}).get("value", "")
            description = binding.get("description", {}).get("value", "")
            parent = binding.get("parent", {}).get("value", "")

            if uri not in classes:
                # 提取 ID
                id_part = uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]
                classes[uri] = {
                    "uri": uri,
                    "id": id_part,
                    "label": label,
                    "description": description,
                    "type": "class",
                    "parents": []
                }

            if parent:
                classes[uri]["parents"].append(parent)

        return list(classes.values())
    except Exception as e:
        print(f"  下载 {subject} class 失败: {e}")
        return []


def download_subject_metadata(subject: str) -> Dict:
    """
    下载学科的完整元数据（category + class）
    """
    print(f"\n下载 {SUBJECT_NAMES.get(subject, subject)} 元数据...")

    metadata = {
        "subject": subject,
        "subject_name": SUBJECT_NAMES.get(subject, subject),
        "graph_iri": f"http://edukb.org/{subject}",
        "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "categories": [],
        "classes": []
    }

    # 下载 category
    categories = download_subject_categories(subject)
    if categories:
        print(f"  category: {len(categories)} 条")
        metadata["categories"] = categories

    # 下载 class
    classes = download_subject_classes(subject)
    if classes:
        print(f"  class: {len(classes)} 条")
        metadata["classes"] = classes

    return metadata


def main():
    print("=" * 70)
    print("EDUKG 学科元数据下载（Category + Class）")
    print("=" * 70)

    all_metadata = {}
    stats = {}

    for subject in tqdm(SUBJECTS, desc="学科进度"):
        metadata = download_subject_metadata(subject)
        all_metadata[subject] = metadata
        stats[subject] = {
            "categories": len(metadata["categories"]),
            "classes": len(metadata["classes"])
        }

        # 保存单学科文件
        output_file = os.path.join(OUTPUT_DIR, f"{subject}_meta.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 保存汇总文件
    summary = {
        "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "subjects": stats,
        "total_categories": sum(s["categories"] for s in stats.values()),
        "total_classes": sum(s["classes"] for s in stats.values())
    }

    summary_file = os.path.join(OUTPUT_DIR, "meta_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # 打印统计
    print("\n" + "=" * 70)
    print("下载完成！统计信息：")
    print("=" * 70)
    print(f"\n{'学科':<10} {'Category':>10} {'Class':>10}")
    print("-" * 35)
    for subject, s in stats.items():
        name = SUBJECT_NAMES.get(subject, subject)
        print(f"{name:<10} {s['categories']:>10} {s['classes']:>10}")
    print("-" * 35)
    print(f"{'合计':<10} {summary['total_categories']:>10} {summary['total_classes']:>10}")
    print(f"\n数据目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()