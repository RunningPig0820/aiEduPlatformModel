#!/usr/bin/env python3
"""
下载 EDUKB 知识点关联数据
包含 relateTo, subCategory, leftRelate, rightRelate 等关系
"""
import os
import requests
from tqdm import tqdm

SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg")
RELATIONS_DIR = os.path.join(OUTPUT_DIR, "relations")

# EDUKB 图谱（包含知识点关联）
EDUKB_GRAPHS = {
    # 学科知识点（含关联关系）
    "math_relations.ttl": "http://edukb.org/math",
    "physics_relations.ttl": "http://edukb.org/physics",
    "chemistry_relations.ttl": "http://edukb.org/chemistry",
    "biology_relations.ttl": "http://edukb.org/biology",
    "chinese_relations.ttl": "http://edukb.org/chinese",
    "history_relations.ttl": "http://edukb.org/history",
    "geo_relations.ttl": "http://edukb.org/geo",
    "politics_relations.ttl": "http://edukb.org/politics",
    "english_relations.ttl": "http://edukb.org/english",
}


def download_graph(graph_iri: str, output_path: str) -> bool:
    """从 SPARQL 端点导出 TTL 文件"""
    query = f"CONSTRUCT {{ ?s ?p ?o }} FROM <{graph_iri}> WHERE {{ ?s ?p ?o . }}"
    headers = {"Accept": "text/turtle"}

    try:
        response = requests.get(
            SPARQL_ENDPOINT,
            params={"query": query},
            headers=headers,
            timeout=300
        )

        if response.status_code == 200:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            return True
        else:
            print(f"  请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"  错误: {e}")
        return False


def count_relations(graph_iri: str) -> dict:
    """统计图谱中的关系数量"""
    relations = {}

    # 统计关键关系
    relation_predicates = [
        ("relateTo", "http://edukb.org/knowledge/0.1/property/common#relateTo"),
        ("belongsTo", "http://edukb.org/knowledge/0.1/property/common#belongsTo"),
        ("partOf", "http://edukb.org/knowledge/0.1/property/common#partOf"),
        ("subCategory", "http://edukb.org/knowledge/0.1/property/common#subCategory"),
        ("superCategory", "http://edukb.org/knowledge/0.1/property/common#superCategory"),
        ("leftRelate", "http://edukb.org/knowledge/0.1/property/common#leftRelate"),
        ("rightRelate", "http://edukb.org/knowledge/0.1/property/common#rightRelate"),
    ]

    headers = {"Accept": "application/sparql-results+json"}

    for name, predicate in relation_predicates:
        query = f"""
        SELECT (COUNT(*) AS ?count)
        FROM <{graph_iri}>
        WHERE {{ ?s <{predicate}> ?o }}
        """
        try:
            response = requests.get(
                SPARQL_ENDPOINT,
                params={"query": query, "format": "json"},
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                count = int(result["results"]["bindings"][0]["count"]["value"])
                if count > 0:
                    relations[name] = count
        except:
            pass

    return relations


def main():
    print("=" * 70)
    print("EDUKB 知识点关联数据下载")
    print("=" * 70)

    os.makedirs(RELATIONS_DIR, exist_ok=True)

    print("\n下载包含知识点关联的 EDUKB 图谱...")

    for filename, graph_iri in tqdm(EDUKB_GRAPHS.items()):
        output_path = os.path.join(RELATIONS_DIR, filename)

        if os.path.exists(output_path):
            print(f"\n  {filename}: 已存在，跳过")
            continue

        print(f"\n  下载 {filename}...")

        # 先统计关系
        relations = count_relations(graph_iri)
        if relations:
            print(f"    关系统计: {relations}")

        # 下载
        if download_graph(graph_iri, output_path):
            size = os.path.getsize(output_path) / 1024 / 1024
            print(f"    成功 ({size:.2f} MB)")
        else:
            print(f"    失败")

    # 汇总
    print("\n" + "=" * 70)
    print("下载完成")
    print("=" * 70)

    ttl_files = [f for f in os.listdir(RELATIONS_DIR) if f.endswith('.ttl')]
    total_size = sum(os.path.getsize(os.path.join(RELATIONS_DIR, f)) for f in ttl_files)

    print(f"\n关联数据文件: {len(ttl_files)} 个")
    print(f"总大小: {total_size / 1024 / 1024:.2f} MB")
    print(f"数据目录: {RELATIONS_DIR}")


if __name__ == "__main__":
    main()