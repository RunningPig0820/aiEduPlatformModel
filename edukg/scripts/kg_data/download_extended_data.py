#!/usr/bin/env python3
"""
下载 EDUKG/EDUKB 所有扩展数据
"""
import os
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

SPARQL_ENDPOINT = "http://39.97.172.123:8890/sparql"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "..", "data", "edukg")
EXTENDED_DIR = os.path.join(OUTPUT_DIR, "extended")

# 所有扩展图谱
EXTENDED_GRAPHS = {
    # 语文扩展
    "chinese_chengyu.ttl": "http://edukb.org/chinese_chengyu",
    "chinese_cidian.ttl": "http://edukb.org/chinese_cidian",
    "chinese_guji.ttl": "http://edukb.org/chinese_guji",
    "chinese_gushiwen.ttl": "http://edukb.org/chinese_gushiwen",
    "chinese_zidian.ttl": "http://edukb.org/chinese_zidian",
    "chinese_zuopin.ttl": "http://edukb.org/chinese_zuopin",

    # 英语扩展
    "english_cidian.ttl": "http://edukb.org/english_cidian",

    # 地理扩展
    "geo_ad_baidu.ttl": "http://edukb.org/geo_ad_baidu",
    "geo_ad_wiki.ttl": "http://edukb.org/geo_ad_wiki",
    "geo_baidu_infobox.ttl": "http://edukb.org/geo_baidu_infobox",
    "geo_baidu_text.ttl": "http://edukb.org/geo_baidu_text",
    "geo_candidate.ttl": "http://edukb.org/geo_candidate",
    "geo_china_admin.ttl": "http://edukb.org/geo_china_administrative_divisions",
    "geo_china_pedia.ttl": "http://edukb.org/geo_china_pedia",
    "geo_geonames.ttl": "http://edukb.org/geo_geonames",
    "geo_resort.ttl": "http://edukb.org/geo_resort",
    "geo_resort_baidu.ttl": "http://edukb.org/geo_resort_baidu",
    "geo_textbook.ttl": "http://edukb.org/geo_textbook",
    "geo_wiki_location.ttl": "http://edukb.org/geo_wiki_location",
    "geo_wiki_text.ttl": "http://edukb.org/geo_wiki_text",

    # 历史扩展
    "history_baidu.ttl": "http://edukb.org/history_baidu",
    "history_baidu_infobox.ttl": "http://edukb.org/history_baidu_infobox",
    "history_pedia.ttl": "http://edukb.org/history_pedia",

    # 其他
    "it.ttl": "http://edukb.org/it",
    "science.ttl": "http://edukb.org/science",
    "tourism.ttl": "http://edukb.org/tourism",

    # EDUKG 版本的扩展
    "edukg_chinese_chengyu.ttl": "http://edukg.org/chinese_chengyu",
    "edukg_chinese_cidian.ttl": "http://edukg.org/chinese_cidian",
    "edukg_chinese_guji.ttl": "http://edukg.org/chinese_guji",
    "edukg_chinese_gushiwen.ttl": "http://edukg.org/chinese_gushiwen",
    "edukg_chinese_zidian.ttl": "http://edukg.org/chinese_zidian",
    "edukg_chinese_zuopin.ttl": "http://edukg.org/chinese_zuopin",
    "edukg_english_cidian.ttl": "http://edukg.org/english_cidian",
}


def download_graph(graph_iri: str, output_path: str) -> tuple:
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
            size = os.path.getsize(output_path) / 1024 / 1024
            return (graph_iri, True, size)
        else:
            return (graph_iri, False, f"HTTP {response.status_code}")
    except Exception as e:
        return (graph_iri, False, str(e))


def main():
    print("=" * 70)
    print("EDUKG/EDUKB 扩展数据下载")
    print("=" * 70)

    os.makedirs(EXTENDED_DIR, exist_ok=True)

    print(f"\n准备下载 {len(EXTENDED_GRAPHS)} 个扩展图谱...")

    success_count = 0
    failed_count = 0
    total_size = 0

    for filename, graph_iri in tqdm(EXTENDED_GRAPHS.items()):
        output_path = os.path.join(EXTENDED_DIR, filename)

        if os.path.exists(output_path):
            size = os.path.getsize(output_path) / 1024 / 1024
            if size > 0.01:  # 大于 10KB 认为有效
                print(f"\n  {filename}: 已存在 ({size:.2f} MB)")
                success_count += 1
                total_size += size
                continue

        print(f"\n  下载 {filename}...", end=" ")

        result = download_graph(graph_iri, output_path)
        graph_iri, success, info = result

        if success:
            print(f"成功 ({info:.2f} MB)")
            success_count += 1
            total_size += info
        else:
            print(f"失败: {info}")
            failed_count += 1

    # 汇总
    print("\n" + "=" * 70)
    print("下载完成")
    print("=" * 70)
    print(f"\n成功: {success_count} 个")
    print(f"失败: {failed_count} 个")
    print(f"总大小: {total_size:.2f} MB")
    print(f"数据目录: {EXTENDED_DIR}")


if __name__ == "__main__":
    main()