#!/usr/bin/env python3
"""
EDUKG 数据下载脚本
从 EDUKG SPARQL 端点导出知识图谱数据
"""
import os
import requests
import json
from tqdm import tqdm

# EDUKG SPARQL 端点
SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"

# 学科列表
SUBJECTS = ["biology", "chemistry", "chinese", "geo", "history", "math", "physics", "politics"]

# 输出目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg")


def query_sparql(query: str, format: str = "json") -> dict:
    """执行 SPARQL 查询"""
    headers = {"Accept": f"application/sparql-results+{format}"}
    params = {"query": query, "format": format}
    response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()


def get_graph_stats(graph_iri: str) -> int:
    """获取图的三元组数量"""
    query = f"SELECT (COUNT(*) AS ?count) FROM <{graph_iri}> WHERE {{ ?s ?p ?o . }}"
    result = query_sparql(query)
    return int(result["results"]["bindings"][0]["count"]["value"])


def export_graph_turtle(graph_iri: str, output_file: str, batch_size: int = 10000):
    """
    导出图数据为 Turtle 格式
    由于 EDUKG 数据量大，采用分批导出
    """
    print(f"正在导出: {graph_iri}")

    # 获取三元组总数
    try:
        total = get_graph_stats(graph_iri)
        print(f"  三元组总数: {total:,}")
    except Exception as e:
        print(f"  无法获取统计信息: {e}")
        return False

    if total == 0:
        print(f"  图为空，跳过")
        return False

    # 查询所有三元组
    all_triplets = []

    # 使用 SPARQL CONSTRUCT 获取 Turtle 格式
    # 注意：由于数据量大，这里使用 SELECT 分批获取
    query = f"""
    CONSTRUCT {{ ?s ?p ?o }}
    FROM <{graph_iri}>
    WHERE {{ ?s ?p ?o . }}
    """

    try:
        # 尝试直接获取 CONSTRUCT 结果
        headers = {"Accept": "text/turtle"}
        params = {"query": query}
        response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=300)

        if response.status_code == 200:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"  已保存: {output_file}")
            return True
        else:
            print(f"  请求失败: {response.status_code}")
            return False

    except Exception as e:
        print(f"  导出失败: {e}")
        return False


def export_subject_entities(subject: str, output_file: str):
    """
    导出学科实体列表（简化版）
    获取实体 URI 和标签
    """
    graph_iri = f"http://edukg.org/{subject}"
    print(f"正在导出实体列表: {subject}")

    query = f"""
    SELECT ?s ?label
    FROM <{graph_iri}>
    WHERE {{
        ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label .
    }}
    LIMIT 50000
    """

    try:
        result = query_sparql(query)
        entities = []
        for binding in result["results"]["bindings"]:
            entities.append({
                "uri": binding["s"]["value"],
                "label": binding["label"]["value"]
            })

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(entities, f, ensure_ascii=False, indent=2)

        print(f"  已保存 {len(entities)} 个实体: {output_file}")
        return True

    except Exception as e:
        print(f"  导出失败: {e}")
        return False


def main():
    print("=" * 60)
    print("EDUKG 数据下载工具")
    print("=" * 60)

    # 1. 测试 SPARQL 端点连接
    print("\n[1/3] 测试 SPARQL 端点连接...")
    try:
        # 查询所有图
        query = "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } }"
        result = query_sparql(query)
        graphs = [b["g"]["value"] for b in result["results"]["bindings"]]
        print(f"  连接成功！发现 {len(graphs)} 个知识图谱")
        for g in graphs[:10]:
            print(f"    - {g}")
        if len(graphs) > 10:
            print(f"    ... 还有 {len(graphs) - 10} 个")
    except Exception as e:
        print(f"  连接失败: {e}")
        print("  请检查网络连接或使用 VPN")
        return

    # 2. 导出各学科实体列表
    print("\n[2/3] 导出学科实体列表...")
    entities_dir = os.path.join(OUTPUT_DIR, "entities")
    os.makedirs(entities_dir, exist_ok=True)

    for subject in tqdm(SUBJECTS, desc="  导出进度"):
        output_file = os.path.join(entities_dir, f"{subject}_entities.json")
        export_subject_entities(subject, output_file)

    # 3. 尝试导出完整的 Turtle 文件（可选）
    print("\n[3/3] 尝试导出 Turtle 文件...")
    turtle_dir = os.path.join(OUTPUT_DIR, "ttl")
    os.makedirs(turtle_dir, exist_ok=True)

    for subject in SUBJECTS[:2]:  # 先尝试前两个学科
        graph_iri = f"http://edukg.org/{subject}"
        output_file = os.path.join(turtle_dir, f"{subject}.ttl")
        export_graph_turtle(graph_iri, output_file)

    print("\n" + "=" * 60)
    print("下载完成！")
    print(f"数据目录: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()