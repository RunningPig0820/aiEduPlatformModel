#!/usr/bin/env python
"""
split_material_ttl.py - 按学科拆分 material.ttl 文件

将 EduKG material.ttl 文件按学科拆分为独立的 material-{subject}.ttl 文件。
教材信息通过教材名称（P4 属性）中的学科关键词识别学科归属。

改进点：
- 使用 RDF 类型 C3 识别教材实体（而非 URI 模式）
- 正确的关系传播列表（移除 P5 hasImage）
- 添加 --skip-unknown 选项
- 添加依赖检查

Usage:
    python split_material_ttl.py --input material.ttl --output-dir edukg/split/
    python split_material_ttl.py --auto-discover  # 自动发现学科
    python split_material_ttl.py --skip-unknown   # 跳过未知学科
"""

import argparse
import logging
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Optional

# 依赖检查
try:
    from rdflib import Graph, URIRef, RDF, RDFS
except ImportError:
    print("Error: rdflib is required. Install with: pip install rdflib")
    sys.exit(1)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ 常量定义 ============

# 学科关键词映射（教材名称 -> 学科代码）
SUBJECT_KEYWORDS = {
    '数学': 'math',
    '物理': 'physics',
    '化学': 'chemistry',
    '生物': 'biology',
    '生物学': 'biology',
    '历史': 'history',
    '地理': 'geo',
    '语文': 'chinese',
    '英语': 'english',
    '思想政治': 'politics',
    '政治': 'politics',
}

# 默认学科列表
DEFAULT_SUBJECTS = list(set(SUBJECT_KEYWORDS.values()))

# 教材类型 URI（C3 = Textbook）
TEXTBOOK_CLASS_URI = URIRef("http://edukg.org/knowledge/3.0/ontology/class/resource#C3")

# 教材名称属性 URI（P4 = name）
NAME_PROPERTY_URI = URIRef("http://edukg.org/knowledge/3.0/ontology/data_property/resource#P4")

# 图片路径属性 URI（P7 = imagePath，用于 C9 图片资源）
IMAGE_PATH_PROPERTY_URI = URIRef("http://edukg.org/knowledge/3.0/ontology/data_property/resource#P7")

# 父子关系列表（仅包含真实的包含关系）
# P13: hasLesson（教材 → 章）
# P2: hasUnit（章 → 单元）
# P3: hasSection（单元 → 节）
# 注意：P5 是 hasImage，不是包含关系，已移除
PARENT_CHILD_RELATIONS = [
    "http://edukg.org/knowledge/3.0/ontology/obj_property/resource#P13",  # hasLesson
    "http://edukg.org/knowledge/3.0/ontology/obj_property/resource#P2",   # hasUnit
    "http://edukg.org/knowledge/3.0/ontology/obj_property/resource#P3",   # hasSection
]


def extract_subject_from_name(name: str) -> str:
    """
    从教材名称中提取学科代码。

    Args:
        name: 教材名称，如 "高中数学必修第一册A版"

    Returns:
        学科代码，未匹配返回 "unknown"
    """
    for keyword, subject in SUBJECT_KEYWORDS.items():
        if keyword in name:
            return subject
    return "unknown"


def is_textbook_entity(graph: Graph, entity_uri: URIRef) -> bool:
    """
    判断实体是否为教材（通过 RDF 类型 C3）。

    Args:
        graph: RDF 图
        entity_uri: 实体 URI

    Returns:
        是否为教材实体
    """
    return (entity_uri, RDF.type, TEXTBOOK_CLASS_URI) in graph


def get_entity_name(graph: Graph, entity_uri: URIRef) -> Optional[str]:
    """
    获取实体名称（P4 属性）。

    Args:
        graph: RDF 图
        entity_uri: 实体 URI

    Returns:
        实体名称
    """
    for obj in graph.objects(entity_uri, NAME_PROPERTY_URI):
        return str(obj)
    return None


def get_entity_image_path(graph: Graph, entity_uri: URIRef) -> Optional[str]:
    """
    获取实体图片路径（P7 属性）。
    用于 C9 类型实体（图片资源），路径中包含教材名称。

    Args:
        graph: RDF 图
        entity_uri: 实体 URI

    Returns:
        图片路径
    """
    for obj in graph.objects(entity_uri, IMAGE_PATH_PROPERTY_URI):
        return str(obj)
    return None


def discover_subjects_from_graph(graph: Graph) -> Set[str]:
    """
    从图中自动发现所有学科名。

    Args:
        graph: RDF 图

    Returns:
        发现的学科名集合
    """
    subjects = set()
    for obj in graph.objects(None, NAME_PROPERTY_URI):
        name = str(obj)
        subject = extract_subject_from_name(name)
        if subject != "unknown":
            subjects.add(subject)
    return subjects


def build_entity_graph(graph: Graph) -> Dict[str, str]:
    """
    构建实体关联图，确定每个实体的学科归属。
    通过关系传播学科：教材 → 章节 → 子章节

    改进点：
    - 使用 RDF 类型 C3 识别教材
    - 对于章节类型（C4/C5/C6）也尝试从名称识别学科
    - 对于图片资源（C9），从图片路径中识别学科
    - 仅使用正确的包含关系（P13, P2, P3）

    Args:
        graph: RDF 图

    Returns:
        实体学科映射
    """
    entity_subject: Dict[str, str] = {}

    # 要识别的实体类型
    # C3: Textbook（教材）- 从 P4 名称识别
    # C4: Chapter（章）- 从 P4 名称识别
    # C5: Section（节）- 从 P4 名称识别
    # C6: SubSection（子节）- 从 P4 名称识别
    # C9: Image（图片）- 从 P7 图片路径识别
    ENTITY_CLASS_URIS_WITH_NAME = [
        URIRef("http://edukg.org/knowledge/3.0/ontology/class/resource#C3"),  # Textbook
        URIRef("http://edukg.org/knowledge/3.0/ontology/class/resource#C4"),  # Chapter
        URIRef("http://edukg.org/knowledge/3.0/ontology/class/resource#C5"),  # Section
        URIRef("http://edukg.org/knowledge/3.0/ontology/class/resource#C6"),  # SubSection
    ]
    ENTITY_CLASS_URI_IMAGE = URIRef("http://edukg.org/knowledge/3.0/ontology/class/resource#C9")  # Image

    # 1. 从 P4 名称识别学科
    entities_with_subject: Dict[str, str] = {}
    textbook_count = 0

    for class_uri in ENTITY_CLASS_URIS_WITH_NAME:
        for s, p, o in graph.triples((None, RDF.type, class_uri)):
            uri = str(s)
            name = get_entity_name(graph, s)
            if name:
                subject = extract_subject_from_name(name)
                if subject != "unknown":
                    entities_with_subject[uri] = subject
                    entity_subject[uri] = subject
                    if class_uri == TEXTBOOK_CLASS_URI:
                        textbook_count += 1

    # 2. 从 P7 图片路径识别学科（C9 类型）
    image_count = 0
    for s, p, o in graph.triples((None, RDF.type, ENTITY_CLASS_URI_IMAGE)):
        uri = str(s)
        image_path = get_entity_image_path(graph, s)
        if image_path:
            subject = extract_subject_from_name(image_path)
            if subject != "unknown":
                entities_with_subject[uri] = subject
                entity_subject[uri] = subject
                image_count += 1

    logger.info(f"Found {textbook_count} textbook entities with subject")
    logger.info(f"Found {image_count} image entities with subject from path")
    logger.info(f"Found {len(entities_with_subject)} total entities with subject")

    # 3. 构建父子关系图
    parent_to_children: Dict[str, Set[str]] = defaultdict(set)
    for pred_uri in PARENT_CHILD_RELATIONS:
        pred = URIRef(pred_uri)
        for s, o in graph.subject_objects(pred):
            parent_to_children[str(s)].add(str(o))

    # 4. BFS 传播学科归属
    def propagate_subject(parent_uri: str, subject: str, visited: Set[str]):
        """递归传播学科到子实体"""
        for child_uri in parent_to_children.get(parent_uri, []):
            if child_uri not in entity_subject and child_uri not in visited:
                entity_subject[child_uri] = subject
                visited.add(child_uri)
                propagate_subject(child_uri, subject, visited)

    for entity_uri, subject in entities_with_subject.items():
        propagate_subject(entity_uri, subject, set())

    # 5. 处理剩余实体（标记为 unknown）
    for s, _, _ in graph:
        s_uri = str(s)
        if s_uri not in entity_subject:
            entity_subject[s_uri] = "unknown"

    # 统计
    subject_counts = defaultdict(int)
    for s in entity_subject.values():
        subject_counts[s] += 1
    for subject, count in sorted(subject_counts.items()):
        logger.info(f"  {subject}: {count} entities")

    return entity_subject


def extract_ttl_headers(content: str) -> str:
    """
    提取 TTL 文件的所有头部定义。

    Args:
        content: TTL 文件内容

    Returns:
        头部定义部分
    """
    lines = content.split('\n')
    header_lines = []

    for line in lines:
        stripped = line.strip()
        if (stripped.startswith('@prefix') or
            stripped.startswith('@base') or
            stripped.startswith('PREFIX') or
            stripped.startswith('BASE')):
            header_lines.append(line)
        elif stripped and not stripped.startswith('#'):
            break

    return '\n'.join(header_lines)


def split_ttl_by_subject(
    input_path: Path,
    output_dir: Path,
    subjects: Optional[List[str]] = None,
    auto_discover: bool = False,
    skip_unknown: bool = False
) -> Dict[str, int]:
    """
    按学科拆分 material.ttl。

    Args:
        input_path: 输入 material.ttl 路径
        output_dir: 输出目录路径
        subjects: 指定的学科列表（可选）
        auto_discover: 是否自动发现学科
        skip_unknown: 是否跳过未知学科

    Returns:
        各学科三元组数量统计
    """
    logger.info(f"Loading {input_path} with RDFlib...")

    # 读取原始文件内容
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
    if auto_discover:
        discovered = discover_subjects_from_graph(graph)
        if subjects:
            subjects = list(set(subjects) | discovered)
        else:
            subjects = list(discovered)
        logger.info(f"Discovered subjects: {sorted(subjects)}")

    # 构建实体学科映射
    logger.info("Building entity-subject mapping...")
    entity_subject = build_entity_graph(graph)

    # 按学科分组三元组
    logger.info("Grouping triples by subject...")
    subject_triples: Dict[str, List[tuple]] = defaultdict(list)

    for s, p, o in graph:
        s_uri = str(s)
        subject = entity_subject.get(s_uri, "unknown")

        # 跳过未知学科
        if skip_unknown and subject == "unknown":
            continue

        subject_triples[subject].append((s, p, o))

    # 统计
    for subject, triples in sorted(subject_triples.items()):
        logger.info(f"Subject '{subject}': {len(triples):,} triples")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 写入各学科文件
    stats = {}
    written_total = 0

    for subject, triples in subject_triples.items():
        if not triples:
            continue

        output_path = output_dir / f"material-{subject}.ttl"

        # 创建子图
        subgraph = Graph()
        for s, p, o in triples:
            subgraph.add((s, p, o))

        # 序列化
        ttl_content = subgraph.serialize(format='turtle')

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ttl_content)

        stats[subject] = len(triples)
        written_total += len(triples)
        logger.info(f"Created {output_path.name}: {len(triples):,} triples")

    # 验证
    if skip_unknown:
        skipped = total_triples - written_total
        logger.info(f"Validation: Original={total_triples:,}, Written={written_total:,}, Skipped={skipped:,}")
    else:
        logger.info(f"Validation: Original={total_triples:,}, Written={written_total:,}")
        if total_triples == written_total:
            logger.info("✓ Validation passed: triple counts match")
        else:
            logger.error(f"✗ Validation failed: {total_triples:,} != {written_total:,}")

    return stats


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='按学科拆分 material.ttl 文件'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/edukg/edukg/material.ttl'),
        help='输入 material.ttl 文件路径'
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
        help='指定学科列表，逗号分隔'
    )
    parser.add_argument(
        '--auto-discover',
        action='store_true',
        help='自动从数据中发现学科名'
    )
    parser.add_argument(
        '--skip-unknown',
        action='store_true',
        help='跳过无法识别学科的实体'
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
        auto_discover=args.auto_discover,
        skip_unknown=args.skip_unknown
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