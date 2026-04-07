"""
知识点对比服务

对比课标提取的知识点与 Neo4j 中已有的 Concept
"""
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from edukg.core.neo4j import get_neo4j_client
from edukg.config.settings import settings


@dataclass
class ComparisonResult:
    """单个知识点对比结果"""
    knowledge_point: str
    status: str  # matched, partial_match, new
    concept_label: Optional[str] = None
    suggested_types: list[str] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class ComparisonReport:
    """对比报告"""
    comparison_at: str
    total_extracted: int
    matched_count: int
    new_count: int
    match_rate: str
    results: list[dict]
    by_stage: dict = field(default_factory=dict)


class ConceptComparator:
    """
    知识点对比服务

    对比课标知识点与 Neo4j 中已有的 Concept
    """

    def __init__(self):
        """初始化对比服务"""
        self.neo4j_client = get_neo4j_client()
        self._concepts_cache: Optional[set[str]] = None

    def _get_all_concepts(self) -> set[str]:
        """
        获取所有 Concept 的 label

        Returns:
            Concept label 集合
        """
        if self._concepts_cache is not None:
            return self._concepts_cache

        query = """
        MATCH (c:Concept)
        WHERE c.label IS NOT NULL
        RETURN c.label AS label
        """

        results = self.neo4j_client.execute_read(query)
        self._concepts_cache = {r["label"] for r in results if r.get("label")}

        return self._concepts_cache

    def _find_partial_match(self, kp: str, concepts: set[str]) -> Optional[str]:
        """
        查找部分匹配的 Concept

        Args:
            kp: 知识点名称
            concepts: Concept 集合

        Returns:
            部分匹配的 Concept label，如果没有则返回 None
        """
        kp_lower = kp.lower()

        for concept in concepts:
            concept_lower = concept.lower()

            # 检查包含关系
            if kp_lower in concept_lower or concept_lower in kp_lower:
                return concept

            # 检查关键词匹配
            kp_words = set(kp_lower)
            concept_words = set(concept_lower)

            # 如果有超过 50% 的字符相同
            if kp_words and concept_words:
                overlap = len(kp_words & concept_words)
                if overlap / len(kp_words) > 0.5:
                    return concept

        return None

    def compare_knowledge_point(
        self,
        kp: str,
        concepts: set[str],
    ) -> ComparisonResult:
        """
        对比单个知识点

        Args:
            kp: 知识点名称
            concepts: Concept 集合

        Returns:
            对比结果
        """
        # 精确匹配
        if kp in concepts:
            return ComparisonResult(
                knowledge_point=kp,
                status="matched",
                concept_label=kp,
                confidence=1.0,
            )

        # 部分匹配
        partial_match = self._find_partial_match(kp, concepts)
        if partial_match:
            return ComparisonResult(
                knowledge_point=kp,
                status="partial_match",
                concept_label=partial_match,
                confidence=0.7,
            )

        # 新知识点
        return ComparisonResult(
            knowledge_point=kp,
            status="new",
            suggested_types=["数学概念"],  # 默认建议类型
            confidence=0.0,
        )

    def compare_from_curriculum_kps(
        self,
        curriculum_kps_path: str,
        verbose: bool = True,
    ) -> ComparisonReport:
        """
        从 curriculum_kps.json 文件对比知识点

        Args:
            curriculum_kps_path: 知识点文件路径
            verbose: 是否显示进度

        Returns:
            对比报告
        """
        curriculum_kps_path = Path(curriculum_kps_path)
        if not curriculum_kps_path.exists():
            raise FileNotFoundError(f"知识点文件不存在: {curriculum_kps_path}")

        with open(curriculum_kps_path, encoding="utf-8") as f:
            data = json.load(f)

        # 获取所有 Concept
        if verbose:
            print("正在从 Neo4j 获取 Concept...")

        concepts = self._get_all_concepts()

        if verbose:
            print(f"获取到 {len(concepts)} 个 Concept")

        # 对比知识点
        results = []
        by_stage = {}
        matched_count = 0
        new_count = 0

        for stage_data in data.get("stages", []):
            stage_name = stage_data.get("stage", "")
            stage_stats = {"total": 0, "matched": 0, "new": 0}

            for domain_data in stage_data.get("domains", []):
                for kp in domain_data.get("knowledge_points", []):
                    if not kp:
                        continue

                    result = self.compare_knowledge_point(kp, concepts)
                    results.append({
                        "knowledge_point": result.knowledge_point,
                        "status": result.status,
                        "concept_label": result.concept_label,
                        "suggested_types": result.suggested_types,
                        "confidence": result.confidence,
                    })

                    stage_stats["total"] += 1

                    if result.status == "matched":
                        matched_count += 1
                        stage_stats["matched"] += 1
                    elif result.status == "new":
                        new_count += 1
                        stage_stats["new"] += 1
                    else:
                        # partial_match 算作 matched
                        matched_count += 1
                        stage_stats["matched"] += 1

            by_stage[stage_name] = stage_stats

        total_extracted = len(results)
        match_rate = f"{matched_count / total_extracted * 100:.1f}%" if total_extracted > 0 else "0%"

        report = ComparisonReport(
            comparison_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            total_extracted=total_extracted,
            matched_count=matched_count,
            new_count=new_count,
            match_rate=match_rate,
            results=results,
            by_stage=by_stage,
        )

        if verbose:
            print(f"对比完成: {total_extracted} 个知识点, 匹配率 {match_rate}")
            print(f"  - 已匹配: {matched_count}")
            print(f"  - 新增: {new_count}")

        return report

    def save_report(self, report: ComparisonReport, output_path: str) -> None:
        """
        保存对比报告

        Args:
            report: 对比报告
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "comparison_at": report.comparison_at,
            "total_extracted": report.total_extracted,
            "matched_count": report.matched_count,
            "new_count": report.new_count,
            "match_rate": report.match_rate,
            "results": report.results,
            "by_stage": report.by_stage,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"对比报告已保存到: {output_path}")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="知识点对比")
    parser.add_argument("--kps", required=True, help="curriculum_kps.json 文件路径")
    parser.add_argument("--output", default="kp_comparison_report.json", help="输出文件路径")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    comparator = ConceptComparator()
    report = comparator.compare_from_curriculum_kps(
        curriculum_kps_path=args.kps,
        verbose=True,
    )
    comparator.save_report(report, args.output)