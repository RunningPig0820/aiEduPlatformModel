"""
Step 4: 概念聚合器

从 teaching_kps_parsed.json 提取核心概念，生成最终的 concepts.json

功能：
1. 提取核心概念并去重
2. 区分已存在（0.1）和新增（0.2）概念
3. 过滤非核心数学概念
4. 关联原始教学知识点

输入: teaching_kps_parsed.json
输出: concepts_v3.json
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Set
from collections import defaultdict

from .config import settings
from .kg_builder import URIGenerator, KGConfig


# 非核心数学概念关键词（需要过滤）
NON_CORE_KEYWORDS = [
    "购物", "招聘", "营养", "水", "游戏", "故事",
    "活动", "经验", "意识", "能力", "素养",
    "问题提出", "问题抽象", "图案设计", "图案",
    "厚度", "尺子", "预测", "趋势",
]


class ConceptAggregator:
    """
    概念聚合器

    从解析后的教学知识点中提取核心概念
    """

    def __init__(self):
        self.uri_generator = URIGenerator(version="0.2", subject="math")

    def is_core_math_concept(self, label: str) -> bool:
        """
        判断是否为核心数学概念

        Args:
            label: 概念标签

        Returns:
            是否为核心数学概念
        """
        # 过滤非核心关键词
        for keyword in NON_CORE_KEYWORDS:
            if keyword in label:
                return False

        # 过滤太短或太长的标签
        if len(label) < 1 or len(label) > 20:
            return False

        return True

    def aggregate(
        self,
        teaching_kps_path: str,
        output_path: str,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """
        聚合核心概念

        Args:
            teaching_kps_path: teaching_kps_parsed.json 路径
            output_path: 输出文件路径
            verbose: 显示进度

        Returns:
            统计信息
        """
        # 加载数据
        with open(teaching_kps_path, encoding="utf-8") as f:
            data = json.load(f)

        teaching_kps = data.get("teaching_knowledge_points", [])

        # 按 URI 聚合
        concepts_by_uri: Dict[str, Dict] = {}
        stats = {
            "total_teaching_kps": len(teaching_kps),
            "existing_concepts": 0,
            "new_concepts": 0,
            "filtered_concepts": 0,
        }

        for tkp in teaching_kps:
            core_concept = tkp.get("core_concept")
            if not core_concept:
                continue

            label = core_concept.get("label", "")
            uri = core_concept.get("uri", "")
            is_existing = core_concept.get("is_existing", False)

            # 过滤非核心概念
            if not self.is_core_math_concept(label):
                stats["filtered_concepts"] += 1
                if verbose:
                    print(f"  过滤: {label}")
                continue

            # 聚合
            if uri not in concepts_by_uri:
                concepts_by_uri[uri] = {
                    "label": label,
                    "uri": uri,
                    "is_existing": is_existing,
                    "types": core_concept.get("types") or [],
                    "teaching_kps": [],
                    "stages": set(),
                    "domains": set(),
                }
                if is_existing:
                    stats["existing_concepts"] += 1
                else:
                    stats["new_concepts"] += 1

            # 关联教学知识点
            concepts_by_uri[uri]["teaching_kps"].append(tkp["original_label"])
            concepts_by_uri[uri]["stages"].add(tkp.get("stage", ""))
            concepts_by_uri[uri]["domains"].add(tkp.get("domain", ""))

        # 转换为列表格式
        concepts = []
        for uri, concept in concepts_by_uri.items():
            concept_data = {
                "label": concept["label"],
                "uri": concept["uri"],
                "version": "0.1" if concept["is_existing"] else "0.2",
                "is_existing": concept["is_existing"],
                "types": concept["types"],
                "teaching_kps": list(set(concept["teaching_kps"])),
                "stages": list(filter(None, concept["stages"])),
                "domains": list(filter(None, concept["domains"])),
            }

            # 新概念需要推断 Class
            if not concept["is_existing"]:
                concept_data["need_class_inference"] = True

            concepts.append(concept_data)

        # 按 label 排序
        concepts.sort(key=lambda x: x["label"])

        # 构建输出
        output_data = {
            "metadata": {
                "total_concepts": len(concepts),
                "existing_concepts": stats["existing_concepts"],
                "new_concepts": stats["new_concepts"],
                "filtered_concepts": stats["filtered_concepts"],
                "total_teaching_kps": stats["total_teaching_kps"],
            },
            "concepts": concepts,
        }

        # 保存
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        if verbose:
            print(f"\n=== Step 4: 概念聚合完成 ===")
            print(f"教学知识点总数: {stats['total_teaching_kps']}")
            print(f"已存在概念: {stats['existing_concepts']} (使用 0.1 URI)")
            print(f"新增概念: {stats['new_concepts']} (使用 0.2 URI)")
            print(f"过滤掉非核心概念: {stats['filtered_concepts']}")
            print(f"输出文件: {output_path}")

        return output_data["metadata"]


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Step 4: 概念聚合")
    parser.add_argument("--input", default="teaching_kps_parsed.json", help="输入文件")
    parser.add_argument("--output", default="concepts_v3.json", help="输出文件")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")

    args = parser.parse_args()

    aggregator = ConceptAggregator()
    aggregator.aggregate(
        teaching_kps_path=args.input,
        output_path=args.output,
        verbose=args.verbose,
    )