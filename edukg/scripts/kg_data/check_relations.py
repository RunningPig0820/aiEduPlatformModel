#!/usr/bin/env python3
"""
查询 EDUKB 中的实际关系实例
"""
import requests

SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"

def query_sparql(query: str, timeout: int = 60) -> dict:
    headers = {"Accept": "application/sparql-results+json"}
    params = {"query": query, "format": "json"}
    response = requests.get(SPARQL_ENDPOINT, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()

def main():
    # 查询 relateTo 的实际实例
    print("=== relateTo 关系实例 ===")
    query = """
    SELECT ?s ?o
    FROM <http://edukb.org/math>
    WHERE { ?s <http://edukb.org/knowledge/0.1/property/common#relateTo> ?o }
    LIMIT 10
    """
    result = query_sparql(query)
    for b in result["results"]["bindings"]:
        s = b["s"]["value"].split("#")[-1]
        o = b["o"]["value"].split("#")[-1]
        print(f"  {s} ->relateTo-> {o}")

    # 查询 subCategory 的实际实例
    print("\n=== subCategory 关系实例 ===")
    query = """
    SELECT ?s ?o
    FROM <http://edukb.org/math>
    WHERE { ?s <http://edukb.org/knowledge/0.1/property/common#subCategory> ?o }
    LIMIT 10
    """
    result = query_sparql(query)
    for b in result["results"]["bindings"]:
        s = b["s"]["value"].split("#")[-1]
        o = b["o"]["value"].split("#")[-1]
        print(f"  {s} ->subCategory-> {o}")

    # 查询 leftRelate 的实际实例
    print("\n=== leftRelate 关系实例 (前置关系?) ===")
    query = """
    SELECT ?s ?o
    FROM <http://edukb.org/math>
    WHERE { ?s <http://edukb.org/knowledge/0.1/property/common#leftRelate> ?o }
    LIMIT 10
    """
    result = query_sparql(query)
    for b in result["results"]["bindings"]:
        s = b["s"]["value"].split("#")[-1]
        o = b["o"]["value"].split("#")[-1]
        print(f"  {s} ->leftRelate-> {o}")

    # 获取实体的标签
    print("\n=== 查看具体知识点关系 (带标签) ===")
    query = """
    SELECT ?sLabel ?p ?oLabel
    FROM <http://edukb.org/math>
    WHERE {
        ?s ?p ?o .
        ?s rdfs:label ?sLabel .
        ?o rdfs:label ?oLabel .
        FILTER(STRSTARTS(STR(?p), "http://edukb.org/knowledge/0.1/property/common#"))
        FILTER(?p != <http://edukb.org/knowledge/0.1/property/common#category>)
        FILTER(?p != <http://edukb.org/knowledge/0.1/property/common#content>)
        FILTER(?p != <http://edukb.org/knowledge/0.1/property/common#page>)
        FILTER(?p != <http://edukb.org/knowledge/0.1/property/common#source>)
    }
    LIMIT 20
    """
    result = query_sparql(query)
    for b in result["results"]["bindings"]:
        sLabel = b.get("sLabel", {}).get("value", "?")
        p = b["p"]["value"].split("#")[-1]
        oLabel = b.get("oLabel", {}).get("value", "?")
        print(f"  {sLabel} --[{p}]--> {oLabel}")

if __name__ == "__main__":
    main()