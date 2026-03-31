#!/usr/bin/env python3
"""
EDUKG all_concept 图数据下载脚本

下载 http://edukg.org/all_concept 图中的 Class 定义
这是跨学科共享的概念类型定义，包含：
- 各学科的 owl:Class 定义
- 类层级关系 (rdfs:subClassOf)
- 标签和描述

使用方法：
    python download_all_concept.py
"""
import os
import json
import requests
from tqdm import tqdm
from typing import Dict, List
import time

# 配置
SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
GRAPH_IRI = "http://edukg.org/all_concept"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg", "concept")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    "english": "英语",
    "k12_education": "K12教育",
}


def query_sparql(query: str, format: str = "json", timeout: int = 120) -> Dict:
    """执行 SPARQL 查询"""
    headers = {"Accept": f"application/sparql-results+{format}"}
    params = {"query": query, "format": format}

    max_retries = 3
    for i in range(max_retries):
        try:
            response = requests.get(
                SPARQL_ENDPOINT, params=params, headers=headers, timeout=timeout
            )
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


def download_graph_stats() -> Dict:
    """下载图统计信息"""
    print("\n[1] 获取 all_concept 图统计信息...")

    # 三元组总数
    query = f"""
    SELECT (COUNT(*) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{ ?s ?p ?o . }}
    """
    result = query_sparql(query)
    triple_count = int(result["results"]["bindings"][0]["count"]["value"])
    print(f"  三元组总数: {triple_count}")

    # Class 总数
    query = f"""
    SELECT (COUNT(DISTINCT ?s) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
    }}
    """
    result = query_sparql(query)
    class_count = int(result["results"]["bindings"][0]["count"]["value"])
    print(f"  Class 总数: {class_count}")

    # 谓词分布
    query = f"""
    SELECT ?p (COUNT(*) AS ?count)
    FROM <{GRAPH_IRI}>
    WHERE {{ ?s ?p ?o . }}
    GROUP BY ?p
    ORDER BY DESC(?count)
    """
    result = query_sparql(query)
    predicates = {}
    for binding in result["results"]["bindings"]:
        pred_uri = binding["p"]["value"]
        count = int(binding["count"]["value"])
        pred_name = pred_uri.split("#")[-1]
        predicates[pred_name] = count
    print(f"  谓词分布: {predicates}")

    return {
        "graph": GRAPH_IRI,
        "triple_count": triple_count,
        "class_count": class_count,
        "predicates": predicates,
    }


def download_all_classes() -> List[Dict]:
    """下载所有 Class 定义"""
    print("\n[2] 下载所有 Class 定义...")

    query = f"""
    SELECT ?s ?label ?description ?type ?parent
    FROM <{GRAPH_IRI}>
    WHERE {{
        ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .
        OPTIONAL {{ ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label . }}
        OPTIONAL {{ ?s <http://purl.org/dc/elements/1.1/description> ?description . }}
        OPTIONAL {{ ?s <http://www.w3.org/2000/01/rdf-schema#subClassOf> ?parent . }}
    }}
    """

    result = query_sparql(query, timeout=180)
    bindings = result["results"]["bindings"]

    # 按实体聚合（因为可能有多个 parent）
    classes = {}
    for binding in bindings:
        uri = binding["s"]["value"]
        label = binding.get("label", {}).get("value", "")
        description = binding.get("description", {}).get("value", "")
        parent = binding.get("parent", {}).get("value", "")

        if uri not in classes:
            # 提取学科和 ID
            if "/class/" in uri:
                subject = uri.split("/class/")[-1].split("#")[0]
                class_id = uri.split("#")[-1]
            else:
                subject = "unknown"
                class_id = uri.split("/")[-1]

            classes[uri] = {
                "uri": uri,
                "id": class_id,
                "subject": subject,
                "label": label,
                "description": description,
                "parents": [],
                "type": "owl:Class",
            }

        if parent:
            classes[uri]["parents"].append(parent)

    class_list = list(classes.values())
    print(f"  下载完成: {len(class_list)} 个 Class")

    return class_list


def organize_by_subject(classes: List[Dict]) -> Dict[str, List[Dict]]:
    """按学科组织 Class 数据"""
    print("\n[3] 按学科组织数据...")

    by_subject = {}
    for cls in classes:
        subject = cls.get("subject", "unknown")
        if subject not in by_subject:
            by_subject[subject] = []
        by_subject[subject].append(cls)

    # 统计
    for subject, cls_list in sorted(by_subject.items()):
        name = SUBJECT_NAMES.get(subject, subject)
        print(f"  {name} ({subject}): {len(cls_list)} 个 Class")

    return by_subject


def build_class_hierarchy(classes: List[Dict]) -> Dict:
    """构建 Class 层级树"""
    print("\n[4] 构建 Class 层级结构...")

    # 创建 URI -> Class 映射
    uri_to_class = {cls["uri"]: cls for cls in classes}

    # 找出根节点（没有 parent 的）
    roots = []
    for cls in classes:
        if not cls["parents"]:
            roots.append(cls)

    print(f"  根节点数量: {len(roots)}")

    # 为每个 Class 添加 children
    children_map = {}
    for cls in classes:
        for parent_uri in cls["parents"]:
            if parent_uri not in children_map:
                children_map[parent_uri] = []
            children_map[parent_uri].append(cls["uri"])

    # 构建层级信息
    hierarchy = {
        "roots": [cls["uri"] for cls in roots],
        "children_map": children_map,
        "uri_to_label": {cls["uri"]: cls["label"] for cls in classes},
    }

    return hierarchy


def save_data(classes: List[Dict], by_subject: Dict, hierarchy: Dict, stats: Dict):
    """保存数据到文件"""
    print("\n[5] 保存数据文件...")

    # 1. 保存完整 Class 列表
    all_classes_file = os.path.join(OUTPUT_DIR, "all_classes.json")
    with open(all_classes_file, "w", encoding="utf-8") as f:
        json.dump(classes, f, ensure_ascii=False, indent=2)
    print(f"  已保存: all_classes.json ({len(classes)} 个)")

    # 2. 保存层级信息
    hierarchy_file = os.path.join(OUTPUT_DIR, "class_hierarchy.json")
    with open(hierarchy_file, "w", encoding="utf-8") as f:
        json.dump(hierarchy, f, ensure_ascii=False, indent=2)
    print(f"  已保存: class_hierarchy.json")

    # 3. 按学科保存
    for subject, cls_list in by_subject.items():
        subject_dir = os.path.join(OUTPUT_DIR, subject)
        os.makedirs(subject_dir, exist_ok=True)

        subject_file = os.path.join(subject_dir, f"{subject}_classes.json")
        with open(subject_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "subject": subject,
                    "subject_name": SUBJECT_NAMES.get(subject, subject),
                    "class_count": len(cls_list),
                    "classes": cls_list,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"  已保存: {subject}/{subject}_classes.json ({len(cls_list)} 个)")

    # 4. 保存汇总报告
    summary = {
        "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "graph": GRAPH_IRI,
        "stats": stats,
        "total_classes": len(classes),
        "subjects": {
            subject: len(cls_list) for subject, cls_list in by_subject.items()
        },
        "output_files": {
            "all_classes": "all_classes.json",
            "hierarchy": "class_hierarchy.json",
            "by_subject": [f"{s}/{s}_classes.json" for s in by_subject.keys()],
        },
    }

    summary_file = os.path.join(OUTPUT_DIR, "download_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"  已保存: download_summary.json")


def main():
    print("=" * 70)
    print("EDUKG all_concept 图数据下载")
    print("=" * 70)
    print(f"SPARQL 端点: {SPARQL_ENDPOINT}")
    print(f"目标图: {GRAPH_IRI}")
    print(f"输出目录: {OUTPUT_DIR}")

    try:
        # 1. 获取统计信息
        stats = download_graph_stats()

        # 2. 下载所有 Class
        classes = download_all_classes()

        # 3. 按学科组织
        by_subject = organize_by_subject(classes)

        # 4. 构建层级
        hierarchy = build_class_hierarchy(classes)

        # 5. 保存数据
        save_data(classes, by_subject, hierarchy, stats)

        print("\n" + "=" * 70)
        print("下载完成！")
        print(f"数据目录: {OUTPUT_DIR}")
        print("=" * 70)

    except Exception as e:
        print(f"\n错误: {e}")
        raise


if __name__ == "__main__":
    main()