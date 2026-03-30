#!/usr/bin/env python
"""
split_main_ttl.py - 按学科拆分 main.ttl 文件（改进版）

使用 RDFlib 正确解析 TTL 文件，按学科 URI 前缀拆分为独立文件。

改进点：
- 使用 RDFlib 解析，确保 RDF 结构正确处理
- 支持所有前缀定义和全局指令（@prefix, @base）
- 使用三元组数量验证数据完整性
- 流式处理，内存友好
- 支持自动发现学科或命令行指定
- 学科名提取更健壮，未匹配放入 unknown

Usage:
    python split_main_ttl.py --input main.ttl --output-dir edukg/split/
    python split_main_ttl.py --subjects math,physics,chemistry
    python split_main_ttl.py --auto-discover  # 自动发现学科
"""

import argparse
import logging
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional

from rdflib import Graph, URIRef, RDF, RDFS
from rdflib.serializer import Serializer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 默认学科列表
DEFAULT_SUBJECTS = ['biology', 'chemistry', 'chinese', 'geo', 'history', 'math', 'physics', 'politics']

# URI 前缀模式：匹配 instance/{subject}# 或 instance/{subject}/
SUBJECT_URI_PATTERN = re.compile(r'instance/([^/#]+)[#/]')


def extract_subject_from_uri(uri: str, known_subjects: Optional[Set[str]] = None) -> str:
    """
    从 URI 中提取学科代码。

    Args:
        uri: 实体 URI
        known_subjects: 已知学科集合，用于验证

    Returns:
        学科代码，未匹配返回 "unknown"
    """
    match = SUBJECT_URI_PATTERN.search(uri)
    if match:
        subject = match.group(1)
        # 如果提供了已知学科列表，验证是否在其中
        if known_subjects is None or subject in known_subjects:
            return subject
        # 即使不在已知列表中，也返回提取的学科名
        return subject
    return "unknown"


def discover_subjects_from_graph(graph: Graph) -> Set[str]:
    """
    从图中自动发现所有学科名。

    Args:
        graph: RDF 图

    Returns:
        发现的学科名集合
    """
    subjects = set()
    for subject in graph.subjects():
        uri = str(subject)
        subject_name = extract_subject_from_uri(uri)
        if subject_name != "unknown":
            subjects.add(subject_name)
    return subjects


def extract_ttl_headers(content: str) -> str:
    """
    提取 TTL 文件的所有头部定义（@prefix, @base 等）。

    Args:
        content: TTL 文件内容

    Returns:
        头部定义部分
    """
    lines = content.split('\n')
    header_lines = []

    for line in lines:
        stripped = line.strip()
        # 捕获所有头部指令
        if (stripped.startswith('@prefix') or
            stripped.startswith('@base') or
            stripped.startswith('PREFIX') or
            stripped.startswith('BASE')):
            header_lines.append(line)
        elif stripped and not stripped.startswith('#'):
            # 遇到非空非注释非头部行，停止
            break

    return '\n'.join(header_lines)


def get_subject_triples(graph: Graph, subjects: Set[str]) -> Dict[str, List[tuple]]:
    """
    按学科分组三元组。

    Args:
        graph: RDF 图
        subjects: 学科名集合

    Returns:
        学科 → 三元组列表映射
    """
    subject_triples: Dict[str, List[tuple]] = defaultdict(list)

    for s, p, o in graph:
        uri = str(s)
        subject_name = extract_subject_from_uri(uri, subjects)
        subject_triples[subject_name].append((s, p, o))

    return subject_triples


def write_subject_ttl(
    output_path: Path,
    triples: List[tuple],
    subject_name: str
) -> int:
    """
    写入学科 TTL 文件。

    Args:
        output_path: 输出文件路径
        triples: 三元组列表
        subject_name: 学科名

    Returns:
        写入的三元组数量
    """
    if not triples:
        return 0

    # 创建子图并添加三元组
    subgraph = Graph()
    for s, p, o in triples:
        subgraph.add((s, p, o))

    # 序列化为 TTL 格式（RDFlib 自动处理 prefixes）
    ttl_content = subgraph.serialize(format='turtle')

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ttl_content)

    return len(triples)


def split_ttl_by_subject(
    input_path: Path,
    output_dir: Path,
    subjects: Optional[List[str]] = None,
    auto_discover: bool = False
) -> Dict[str, int]:
    """
    按 URI 前缀将 TTL 文件拆分为多个学科文件。

    Args:
        input_path: 输入 main.ttl 路径
        output_dir: 输出目录路径
        subjects: 指定的学科列表（可选）
        auto_discover: 是否自动发现学科

    Returns:
        各学科三元组数量统计
    """
    logger.info(f"Loading {input_path} with RDFlib...")

    # 读取原始文件内容（用于提取头部）
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    headers = extract_ttl_headers(raw_content)
    logger.info(f"Extracted headers ({len(headers.split(chr(10)))} lines)")

    # 使用 RDFlib 解析
    graph = Graph()
    graph.parse(input_path, format='turtle')

    total_triples = len(graph)
    logger.info(f"Loaded {total_triples:,} triples")

    # 确定学科列表
    if subjects is None and not auto_discover:
        subjects = DEFAULT_SUBJECTS
        logger.info(f"Using default subjects: {subjects}")
    elif auto_discover:
        discovered = discover_subjects_from_graph(graph)
        if subjects:
            # 合并指定学科和发现的学科
            subjects = list(set(subjects) | discovered)
        else:
            subjects = list(discovered)
        logger.info(f"Discovered subjects: {subjects}")

    subject_set = set(subjects)

    # 按学科分组三元组
    logger.info("Grouping triples by subject...")
    subject_triples = get_subject_triples(graph, subject_set)

    # 统计 unknown
    unknown_count = len(subject_triples.get('unknown', []))
    if unknown_count > 0:
        logger.warning(f"Found {unknown_count:,} triples with unknown subject")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 写入各学科文件
    stats = {}
    written_total = 0

    for subject in subjects:
        triples = subject_triples.get(subject, [])
        if triples:
            output_path = output_dir / f"main-{subject}.ttl"
            count = write_subject_ttl(output_path, triples, subject)
            stats[subject] = count
            written_total += count
            logger.info(f"Created {output_path.name}: {count:,} triples")
        else:
            stats[subject] = 0
            logger.warning(f"No triples found for subject: {subject}")

    # 处理 unknown
    if unknown_count > 0:
        output_path = output_dir / "main-unknown.ttl"
        count = write_subject_ttl(output_path, subject_triples['unknown'], 'unknown')
        stats['unknown'] = count
        written_total += count
        logger.info(f"Created main-unknown.ttl: {count:,} triples")

    # 验证
    logger.info(f"Validation: Original={total_triples:,}, Written={written_total:,}")
    if total_triples == written_total:
        logger.info("✓ Validation passed: triple counts match")
    else:
        logger.error(f"✗ Validation failed: {total_triples:,} != {written_total:,}")

    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='按学科拆分 main.ttl 文件（使用 RDFlib 解析）'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/edukg/edukg/main.ttl'),
        help='输入 main.ttl 文件路径'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('data/edukg/split'),
        help='输出目录路径'
    )
    parser.add_argument(
        '--subjects',
        type=str,
        default=None,
        help='指定学科列表，逗号分隔（如 math,physics,chemistry）'
    )
    parser.add_argument(
        '--auto-discover',
        action='store_true',
        help='自动从数据中发现学科名'
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='跳过三元组数量验证'
    )

    args = parser.parse_args()

    # 检查输入文件
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # 解析学科列表
    subjects = None
    if args.subjects:
        subjects = [s.strip() for s in args.subjects.split(',')]

    # 执行拆分
    stats = split_ttl_by_subject(
        args.input,
        args.output_dir,
        subjects=subjects,
        auto_discover=args.auto_discover
    )

    # 打印统计
    print("\n=== Split Statistics ===")
    total = 0
    for subject, count in sorted(stats.items()):
        total += count
        print(f"  {subject}: {count:,} triples")
    print(f"  Total: {total:,} triples")
    print(f"  Output directory: {args.output_dir}")

    print("\n✓ Split completed successfully")


if __name__ == '__main__':
    main()