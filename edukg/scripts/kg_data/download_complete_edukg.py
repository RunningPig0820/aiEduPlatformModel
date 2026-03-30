#!/usr/bin/env python3
"""
EDUKG 完整数据下载脚本

包含两部分：
1. 从 SPARQL 端点导出的数据（已下载）
2. 从 Google Drive 下载的数据（需要手动或通过 gdown 下载）
"""
import os
import requests
import json
from typing import Optional

# ============ 配置 ============
SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg")
TTL_DIR = os.path.join(OUTPUT_DIR, "ttl")
ENTITIES_DIR = os.path.join(OUTPUT_DIR, "entities")

# Google Drive 文件 ID（来自 EDUKG README）
GOOGLE_DRIVE_FILES = {
    # 核心概念
    "main.ttl": "1YoPITzjk2oKoX0k_XbLplu8IUn16bg4-",  # 主要概念 (16.8M)

    # 阅读材料
    "material.ttl": "1xgUWMkIl5g3h_CeneCPDOR3MUlWyX06q",  # 阅读材料 (3.7M)

    # 外部数据
    "biogrid.zip": "1ed0ec9WdEDuCIdrd7rJOwkyoWtr2Bc5c",  # BioGRID (52.8M)
    "uniprot.zip": "19GqxPKCupUwIOH1OWLRSZ7LdLhKIJ4dQ",  # UniProtKB (410.8M)
    "nytimes.zip": "1ZV21wGPx8oE9XKwijlAIRFlNM6cCpH9A",  # New York Times (544.6M)
    "NBS.zip": "1ItBqExrTXonsyk8EzU9b7lj0HZK536AR",  # NBSC (8.9M)
    "HowNet.zip": "1kZg3ose06wLIYNBJ1XfXmY7GdToR2On1",  # HowNet (8.2M)
    "framester.zip": "1hWSGOAYpgTk5-hrCoijhLI9jPhpPVJ5t",  # Framester (969.7M)
    "geoNames.zip": "1Yve8deeTpQsqjpT2TpTmrktB1vnlECwY",  # GeoNames (459.8M)
}

# SPARQL 端点可导出的图谱
SPARQL_GRAPHS = {
    # 学科知识图谱
    "biology.ttl": "http://edukg.org/biology",
    "chemistry.ttl": "http://edukg.org/chemistry",
    "chinese.ttl": "http://edukg.org/chinese",
    "geo.ttl": "http://edukg.org/geo",
    "history.ttl": "http://edukg.org/history",
    "math.ttl": "http://edukg.org/math",
    "physics.ttl": "http://edukg.org/physics",
    "politics.ttl": "http://edukg.org/politics",
    "english.ttl": "http://edukg.org/english",

    # 核心概念
    "all_concept.ttl": "http://edukg.org/all_concept",
    "all_category.ttl": "http://edukg.org/all_category",
}


def download_from_google_drive(file_id: str, output_path: str) -> bool:
    """
    从 Google Drive 下载文件
    需要安装 gdown: pip install gdown
    """
    try:
        import gdown
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, output_path, quiet=False)
        return True
    except ImportError:
        print("请安装 gdown: pip install gdown")
        return False
    except Exception as e:
        print(f"下载失败: {e}")
        return False


def download_from_sparql(graph_iri: str, output_path: str) -> bool:
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


def export_entities_json(graph_iri: str, output_path: str, limit: int = 50000) -> bool:
    """导出实体列表为 JSON"""
    query = f"""
    SELECT ?s ?label
    FROM <{graph_iri}>
    WHERE {{
        ?s <http://www.w3.org/2000/01/rdf-schema#label> ?label .
    }}
    LIMIT {limit}
    """
    headers = {"Accept": "application/sparql-results+json"}

    try:
        response = requests.get(
            SPARQL_ENDPOINT,
            params={"query": query, "format": "json"},
            headers=headers,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            entities = []
            for binding in result["results"]["bindings"]:
                entities.append({
                    "uri": binding["s"]["value"],
                    "label": binding["label"]["value"]
                })

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)

            return True
        return False
    except Exception as e:
        print(f"  错误: {e}")
        return False


def main():
    print("=" * 70)
    print("EDUKG 数据下载工具")
    print("=" * 70)

    # 创建目录
    os.makedirs(TTL_DIR, exist_ok=True)
    os.makedirs(ENTITIES_DIR, exist_ok=True)

    # 1. 从 SPARQL 端点下载
    print("\n【步骤 1】从 SPARQL 端点导出数据...")
    for filename, graph_iri in SPARQL_GRAPHS.items():
        output_path = os.path.join(TTL_DIR, filename)
        if os.path.exists(output_path):
            print(f"  {filename}: 已存在，跳过")
            continue

        print(f"  导出 {filename}...", end=" ")
        if download_from_sparql(graph_iri, output_path):
            size = os.path.getsize(output_path) / 1024 / 1024
            print(f"成功 ({size:.2f} MB)")
        else:
            print("失败")

    # 2. 从 Google Drive 下载（需要手动确认）
    print("\n【步骤 2】从 Google Drive 下载额外数据...")
    print("\n以下文件需要从 Google Drive 下载（可能需要 VPN）：")
    print("-" * 50)

    for filename, file_id in GOOGLE_DRIVE_FILES.items():
        output_path = os.path.join(TTL_DIR, filename)
        if os.path.exists(output_path):
            print(f"  {filename}: 已存在")
            continue

        print(f"\n  {filename}")
        print(f"    Google Drive ID: {file_id}")
        print(f"    下载链接: https://drive.google.com/file/d/{file_id}/view")

        # 尝试使用 gdown
        if input("    是否尝试自动下载? (y/n): ").lower() == 'y':
            if download_from_google_drive(file_id, output_path):
                print("    下载成功!")

    # 3. 统计
    print("\n" + "=" * 70)
    print("下载完成统计")
    print("=" * 70)

    ttl_files = [f for f in os.listdir(TTL_DIR) if f.endswith('.ttl')]
    json_files = [f for f in os.listdir(ENTITIES_DIR) if f.endswith('.json')]

    total_size = 0
    for f in ttl_files:
        total_size += os.path.getsize(os.path.join(TTL_DIR, f))

    print(f"\nTTL 文件: {len(ttl_files)} 个")
    print(f"实体 JSON: {len(json_files)} 个")
    print(f"总大小: {total_size / 1024 / 1024:.2f} MB")

    print(f"\n数据目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()