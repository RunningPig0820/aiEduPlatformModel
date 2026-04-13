#!/usr/bin/env python3
"""
继续查询 EDUKG 知识点关联数据
"""
import requests

SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"

def query_sparql(query: str, timeout: int = 120) -> dict:
    """执行 SPARQL 查询"""
    headers = {"Accept": "application/sparql-results+json"}
    params = {"query": query, "format": "json"}
    response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()

def main():
    print("=" * 60)
    print("EDUKG 知识点关联探索 (续)")
    print("=" * 60)

    # 1. 检查 all_property 图谱
    print("\n[1] 检查 all_property 图谱...")
    query = """
    SELECT DISTINCT ?p (COUNT(?p) AS ?count)
    FROM <http://edukg.org/all_property>
    WHERE { ?s ?p ?o }
    GROUP BY ?p
    ORDER BY DESC(?count)
    LIMIT 20
    """
    try:
        result = query_sparql(query)
        print("all_property 图谱中的谓词:")
        for b in result["results"]["bindings"]:
            p = b["p"]["value"]
            count = b["count"]["value"]
            print(f"  - {p}: {count}")
    except Exception as e:
        print(f"  查询失败: {e}")

    # 2. 检查 EDUKB 图谱（可能是不同的数据源）
    print("\n[2] 检查 EDUKB 数学图谱...")
    query = """
    SELECT DISTINCT ?p (COUNT(?p) AS ?count)
    FROM <http://edukb.org/math>
    WHERE { ?s ?p ?o }
    GROUP BY ?p
    ORDER BY DESC(?count)
    LIMIT 20
    """
    try:
        result = query_sparql(query)
        print("edukb.org/math 图谱中的谓词:")
        for b in result["results"]["bindings"]:
            p = b["p"]["value"]
            count = b["count"]["value"]
            print(f"  - {p}: {count}")
    except Exception as e:
        print(f"  查询失败: {e}")

    # 3. 检查是否有 rdfs:subClassOf
    print("\n[3] 检查数学图谱中的层级关系...")
    query = """
    SELECT ?s ?o
    FROM <http://edukg.org/math>
    WHERE { ?s rdfs:subClassOf ?o }
    LIMIT 10
    """
    try:
        result = query_sparql(query)
        bindings = result["results"]["bindings"]
        if bindings:
            print("找到 subClassOf 关系:")
            for b in bindings[:10]:
                s = b["s"]["value"]
                o = b["o"]["value"]
                print(f"  {s.split('#')[-1]} -> {o.split('#')[-1]}")
        else:
            print("  未找到 subClassOf 关系")
    except Exception as e:
        print(f"  查询失败: {e}")

    # 4. 检查是否有自定义关系谓词
    print("\n[4] 搜索可能的关系谓词...")
    # 常见的知识点关系关键词
    keywords = ["relation", "link", "connect", "depend", "require",
                "before", "after", "next", "prev", "parent", "child"]

    for kw in keywords[:3]:  # 只检查前3个避免超时
        query = f"""
        SELECT DISTINCT ?p
        WHERE {{
            ?s ?p ?o .
            FILTER(CONTAINS(LCASE(STR(?p)), "{kw}"))
        }}
        LIMIT 10
        """
        try:
            result = query_sparql(query, timeout=30)
            bindings = result["results"]["bindings"]
            if bindings:
                print(f"  包含 '{kw}' 的谓词:")
                for b in bindings:
                    print(f"    - {b['p']['value']}")
        except Exception as e:
            print(f"  查询 '{kw}' 失败: {e}")

    # 5. 查看一个具体的数学知识点有哪些属性
    print("\n[5] 查看具体数学知识点的属性...")
    query = """
    SELECT ?p ?o
    FROM <http://edukg.org/math>
    WHERE {
        ?s rdfs:label "一元二次方程"@zh .
        ?s ?p ?o .
    }
    """
    try:
        result = query_sparql(query)
        print("一元二次方程 的属性:")
        for b in result["results"]["bindings"]:
            p = b["p"]["value"]
            o = b["o"]["value"]
            p_short = p.split("/")[-1] if "/" in p else p.split("#")[-1] if "#" in p else p
            print(f"  {p_short}: {o[:50]}...")
    except Exception as e:
        print(f"  查询失败: {e}")

    # 6. 检查 EDUKB 的 all_property
    print("\n[6] 检查 EDUKB 的属性定义...")
    query = """
    SELECT ?s ?o
    FROM <http://edukb.org/math>
    WHERE { ?s ?p ?o . ?s rdfs:label ?label }
    LIMIT 5
    """
    try:
        result = query_sparql(query, timeout=30)
        print("EDUKB 数学图谱示例:")
        for b in result["results"]["bindings"]:
            print(f"  {b}")
    except Exception as e:
        print(f"  查询失败: {e}")

if __name__ == "__main__":
    main()