#!/usr/bin/env python3
"""
DAG 验证脚本

功能:
1. 验证 PREREQUISITE 关系无环
2. 输出验证报告
3. 计算质量指标（覆盖率、平均链长、置信度分布）

使用方法:
    python validate_dag.py
    python validate_dag.py --report  # 输出详细报告

退出码:
    0: 无环
    1: 有环
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict

# 添加项目根目录到 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from edukg.core.llm_inference.config import (
    OUTPUT_DIR,
    FINAL_PREREQ_FILE,
    VALIDATION_REPORT_FILE,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DAGValidator:
    """DAG 验证器"""

    def __init__(self):
        self.relations: List[Dict] = []
        self.graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_graph: Dict[str, Set[str]] = defaultdict(set)

    def load_relations(self, filepath: str = None) -> List[Dict]:
        """
        加载前置关系数据

        Args:
            filepath: 文件路径（默认使用 final_prereq.json）

        Returns:
            关系列表
        """
        if filepath is None:
            filepath = Path(OUTPUT_DIR) / FINAL_PREREQ_FILE
        else:
            filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            self.relations = json.load(f)

        logger.info(f"加载 {len(self.relations)} 个关系")

        # 构建图
        self._build_graph()

        return self.relations

    def _build_graph(self):
        """构建有向图"""
        for rel in self.relations:
            # 只处理 PREREQUISITE 关系（不包括 TEACHES_BEFORE 和 CANDIDATE）
            if rel.get('relation_type') in ['PREREQUISITE', 'PREREQUISITE_CANDIDATE']:
                kp_a_uri = rel['kp_a_uri']
                kp_b_uri = rel['kp_b_uri']

                # A → B 表示 A 是 B 的前置
                self.graph[kp_a_uri].add(kp_b_uri)
                self.reverse_graph[kp_b_uri].add(kp_a_uri)

        logger.info(f"图节点数: {len(self.graph)}")

    def detect_cycles(self) -> List[List[str]]:
        """
        检测图中的环

        Returns:
            检测到的环列表，每个环是一个节点 URI 列表
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]):
            """DFS 检测环"""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    # 找到环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        # 从所有节点开始 DFS
        for node in list(self.graph.keys()):
            if node not in visited:
                dfs(node, [])

        return cycles

    def calculate_coverage(self) -> float:
        """
        计算覆盖率

        覆盖率 = 有前置关系的知识点数 / 总知识点数

        Returns:
            覆盖率（0.0-1.0）
        """
        # 所有知识点 URI
        all_kps = set()
        for rel in self.relations:
            all_kps.add(rel['kp_a_uri'])
            all_kps.add(rel['kp_b_uri'])

        # 有前置关系的知识点（作为 target）
        has_prereq = set()
        for rel in self.relations:
            if rel.get('relation_type') in ['PREREQUISITE', 'PREREQUISITE_CANDIDATE']:
                has_prereq.add(rel['kp_b_uri'])

        if len(all_kps) == 0:
            return 0.0

        return len(has_prereq) / len(all_kps)

    def calculate_avg_chain_length(self) -> float:
        """
        计算平均链长

        Returns:
            平均链长
        """
        # 找到所有根节点（没有前置关系的节点）
        roots = set()
        for node in self.graph.keys():
            if node not in self.reverse_graph:
                roots.add(node)

        # 计算从根节点到每个节点的最长路径
        max_lengths = {}

        def get_max_length(node: str) -> int:
            """获取从根到该节点的最长路径长度"""
            if node in max_lengths:
                return max_lengths[node]

            prereqs = self.reverse_graph.get(node, set())
            if not prereqs:
                max_lengths[node] = 0
                return 0

            max_len = max(get_max_length(p) for p in prereqs) + 1
            max_lengths[node] = max_len
            return max_len

        for node in self.graph.keys():
            get_max_length(node)

        if not max_lengths:
            return 0.0

        return sum(max_lengths.values()) / len(max_lengths)

    def calculate_confidence_distribution(self) -> Dict[str, float]:
        """
        计算置信度分布

        Returns:
            {'high': 百分比, 'medium': 百分比, 'low': 百分比}
        """
        prereq_relations = [
            r for r in self.relations
            if r.get('relation_type') in ['PREREQUISITE', 'PREREQUISITE_CANDIDATE']
        ]

        if not prereq_relations:
            return {'high': 0, 'medium': 0, 'low': 0}

        high = sum(1 for r in prereq_relations if r.get('confidence', 0) >= 0.8)
        medium = sum(1 for r in prereq_relations if 0.5 <= r.get('confidence', 0) < 0.8)
        low = sum(1 for r in prereq_relations if r.get('confidence', 0) < 0.5)

        total = len(prereq_relations)

        return {
            'high': high / total,
            'medium': medium / total,
            'low': low / total,
            'high_count': high,
            'medium_count': medium,
            'low_count': low,
            'total': total
        }

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """
        执行完整验证

        Returns:
            (is_valid, report) - 是否有效，验证报告
        """
        # 检测环
        cycles = self.detect_cycles()
        is_valid = len(cycles) == 0

        # 计算指标
        coverage = self.calculate_coverage()
        avg_chain_length = self.calculate_avg_chain_length()
        confidence_dist = self.calculate_confidence_distribution()

        report = {
            'is_valid': is_valid,
            'cycle_count': len(cycles),
            'cycles': cycles if cycles else [],
            'coverage': coverage,
            'avg_chain_length': avg_chain_length,
            'confidence_distribution': confidence_dist,
            'total_relations': len(self.relations),
            'prerequisite_count': sum(1 for r in self.relations if r.get('relation_type') == 'PREREQUISITE'),
            'candidate_count': sum(1 for r in self.relations if r.get('relation_type') == 'PREREQUISITE_CANDIDATE'),
        }

        return is_valid, report

    def save_report(self, report: Dict[str, Any]) -> str:
        """
        保存验证报告

        Args:
            report: 验证报告

        Returns:
            保存的文件路径
        """
        output_path = Path(OUTPUT_DIR) / VALIDATION_REPORT_FILE

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"报告保存到: {output_path}")
        return str(output_path)

    def print_report(self, report: Dict[str, Any]):
        """
        打印验证报告

        Args:
            report: 验证报告
        """
        print("\n" + "=" * 50)
        print("DAG VALIDATION REPORT")
        print("=" * 50)

        # 环检测
        cycle_status = "✓" if report['cycle_count'] == 0 else "✗"
        print(f"\nCycle detection: {report['cycle_count']} cycles {cycle_status}")

        if report['cycles']:
            print("\nDetected cycles:")
            for i, cycle in enumerate(report['cycles'][:5], 1):  # 只显示前 5 个
                cycle_str = " → ".join(cycle)
                print(f"  {i}. {cycle_str}")
            if len(report['cycles']) > 5:
                print(f"  ... ({len(report['cycles']) - 5} more cycles)")

        # 覆盖率
        coverage_pct = report['coverage'] * 100
        coverage_status = "✓" if coverage_pct > 50 else "⚠"
        print(f"\nCoverage rate: {coverage_pct:.1f}% {coverage_status}")

        # 平均链长
        print(f"Average chain length: {report['avg_chain_length']:.2f}")

        # 置信度分布
        conf = report['confidence_distribution']
        print("\nConfidence distribution:")
        print(f"  - High (≥0.8): {conf['high'] * 100:.1f}% ({conf['high_count']})")
        print(f"  - Medium (0.5-0.8): {conf['medium'] * 100:.1f}% ({conf['medium_count']})")
        print(f"  - Low (<0.5): {conf['low'] * 100:.1f}% ({conf['low_count']})")

        # 关系数量
        print(f"\nTotal relations: {report['total_relations']}")
        print(f"  - PREREQUISITE: {report['prerequisite_count']}")
        print(f"  - PREREQUISITE_CANDIDATE: {report['candidate_count']}")

        # 结论
        print("\n" + "-" * 50)
        if report['is_valid']:
            print("All validations passed.")
            print("Exit code: 0")
        else:
            print("VALIDATION FAILED - cycles detected!")
            print("Please fix cycles before proceeding.")
            print("Exit code: 1")

        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description='DAG 验证')
    parser.add_argument('--input', type=str, help='输入文件路径（默认使用 final_prereq.json）')
    parser.add_argument('--report', action='store_true', help='输出详细报告')

    args = parser.parse_args()

    validator = DAGValidator()

    try:
        # 加载关系
        validator.load_relations(args.input)

        # 执行验证
        is_valid, report = validator.validate()

        # 打印报告
        validator.print_report(report)

        # 保存报告
        if args.report:
            validator.save_report(report)

        # 设置退出码
        sys.exit(0 if is_valid else 1)

    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()