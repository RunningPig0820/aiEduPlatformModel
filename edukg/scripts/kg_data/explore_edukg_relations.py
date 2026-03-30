#!/usr/bin/env python3
"""
查询 EDUKG SPARQL 端点，寻找知识点关联数据
"""
import requests
import json

SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"

def query_sparql(query: str) -> dict:
    """执行 SPARQL 查询"""
    headers = {"Accept": "application/sparql-results+json"}
    params = {"query": query, "format": "json"}
    response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()

def main():
    print("=" * 60)
    print("EDUKG 数据源探索")
    print("=" * 60)

    # 1. 查询所有图谱
    print("\n[1] 查询所有知识图谱...")
    query = "SELECT DISTINCT ?g WHERE { GRAPH ?g { ?s ?p ?o } } ORDER BY ?g"
    result = query_sparql(query)
    graphs = [b["g"]["value"] for b in result["results"]["bindings"]]
    print(f"发现 {len(graphs)} 个图谱:")
    for g in graphs:
        print(f"  - {g}")

    # 2. 查询所有谓词（关系类型）
    print("\n[2] 查询所有谓词（关系类型）...")
    query = """
    SELECT ?p (COUNT(?p) AS ?count)
    WHERE { ?s ?p ?o }
    GROUP BY ?p
    ORDER BY DESC(?count)
    LIMIT 50
    """
    result = query_sparql(query)
    print("前 50 个谓词:")
    for b in result["results"]["bindings"]:
        p = b["p"]["value"]
        count = b["count"]["value"]
        # 过滤掉标准 RDF 谓词
        if "w3.org" not in p:
            print(f"  - {p}: {count}")

    # 3. 查找可能的前置/后置关系
    print("\n[3] 查找可能的前置/后置关系...")
    keywords = ["prerequisite", "before", "after", "pre", "next", "related",
                "depend", "前继", "后继", "前置", "后置", "关联", "依赖"]

    query = f"""
    SELECT DISTINCT ?p
    WHERE {{
        ?s ?p ?o .
        FILTER(
            CONTAINS(LCASE(STR(?p)), "prerequisite") ||
            CONTAINS(LCASE(STR(?p)), "before") ||
            CONTAINS(LCASE(STR(?p)), "after") ||
            CONTAINS(LCASE(STR(?p)), "pre") ||
            CONTAINS(LCASE(STR(?p)), "next") ||
            CONTAINS(LCASE(STR(?p)), "related") ||
            CONTAINS(LCASE(STR(?p)), "depend") ||
            CONTAINS(LCASE(STR(?p)), "sub")
        )
    }}
    """
    result = query_sparql(query)
    relations = [b["p"]["value"] for b in result["results"]["bindings"]]
    if relations:
        print("找到可能的关系:")
        for r in relations:
            print(f"  - {r}")
    else:
        print("未找到明确的前置/后置关系谓词")

    # 4. 检查 subClassOf 关系
    print("\n[4] 检查层级关系 (subClassOf)...")
    query = """
    SELECT (COUNT(*) AS ?count)
    WHERE { ?s rdfs:subClassOf ?o }
    """
    result = query_sparql(query)
    count = result["results"]["bindings"][0]["count"]["value"]
    print(f"  rdfs:subClassOf 三元组数量: {count}")

    # 5. 检查是否有自定义关系
    print("\n[5] 检查 EDUKG 自定义命名空间...")
    query = """
    SELECT DISTINCT ?p
    WHERE {
        ?s ?p ?o .
        FILTER(STRSTARTS(STR(?p), "http://edukg.org"))
    }
    LIMIT 100
    """
    result = query_sparql(query)
    predicates = [b["p"]["value"] for b in result["results"]["bindings"]]
    print(f"发现 {len(predicates)} 个 EDUKG 自定义谓词:")
    for p in predicates[:30]:
        print(f"  - {p}")

    # 6. 检查特定图谱的关系
    print("\n[6] 检查数学图谱的关系...")
    query = """
    SELECT DISTINCT ?p (COUNT(?p) AS ?count)
    FROM <http://edukg.org/math>
    WHERE { ?s ?p ?o }
    GROUP BY ?p
    ORDER BY DESC(?count)
    """
    result = query_sparql(query)
    print("数学图谱中的谓词:")
    for b in result["results"]["bindings"]:
        p = b["p"]["value"]
        count = b["count"]["value"]
        short_p = p.split("/")[-1] if "/" in p else p.split("#")[-1] if "#" in p else p
        print(f"  - {short_p}: {count}")

if __name__ == "__main__":
    main()