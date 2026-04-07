"""
知识图谱构建主脚本

从 OCR 结果生成完整的知识图谱 JSON 文件:
- classes.json
- concepts.json
- statements.json
- relations.json
"""
import argparse
import json
import time
from pathlib import Path

from .config import settings
from .kp_extraction import LLMExtractor
from .class_extractor import ClassExtractor
from .concept_extractor import ConceptExtractor
from .statement_extractor import StatementExtractor
from .relation_extractor import RelationExtractor
from .kg_builder import KGConfig


def build_knowledge_graph(
    ocr_result_path: str,
    output_dir: str,
    skip_extraction: bool = False,
    verbose: bool = True,
) -> dict:
    """
    从 OCR 结果构建知识图谱

    Args:
        ocr_result_path: OCR 结果 JSON 文件路径
        output_dir: 输出目录
        skip_extraction: 是否跳过知识点提取（使用已有 curriculum_kps.json）
        verbose: 是否显示进度

    Returns:
        构建结果统计
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    # 1. 提取知识点（如果需要）
    kps_path = output_dir / "curriculum_kps.json"

    if not skip_extraction or not kps_path.exists():
        if verbose:
            print("\n" + "=" * 50)
            print("阶段 1: 从 OCR 结果提取知识点")
            print("=" * 50)

        extractor = LLMExtractor()
        result = extractor.extract_from_ocr_result(ocr_result_path, verbose=verbose)
        extractor.save_result(result, str(kps_path))

        total_kps = result.total_knowledge_points
    else:
        if verbose:
            print(f"使用已有的知识点文件: {kps_path}")

        with open(kps_path, encoding="utf-8") as f:
            kps_data = json.load(f)
        total_kps = kps_data.get("total_knowledge_points", 0)

    # 2. 加载知识点列表
    with open(kps_path, encoding="utf-8") as f:
        kps_data = json.load(f)

    knowledge_points = []
    for stage in kps_data.get("stages", []):
        for domain in stage.get("domains", []):
            knowledge_points.extend(domain.get("knowledge_points", []))

    # 去重
    knowledge_points = list(set(knowledge_points))

    if verbose:
        print(f"\n知识点总数: {len(knowledge_points)}")

    # 3. Class 提取
    if verbose:
        print("\n" + "=" * 50)
        print("阶段 2: 推断知识点类型（使用 LLM）")
        print("=" * 50)

    class_extractor = ClassExtractor()
    class_results = class_extractor.batch_infer_types(knowledge_points, verbose=verbose)

    # 收集新的 Class
    new_classes = []
    for result in class_results:
        if result.is_new_class and result.class_label not in [c["label"] for c in new_classes]:
            parent_uri = class_extractor.get_parent_uri(
                result.parent_class if result.parent_class else result.class_label
            )
            new_classes.append(
                class_extractor.generate_class_definition(result.class_label, parent_uri)
            )

    # 保存 classes.json
    classes_path = output_dir / "classes.json"
    class_extractor.save_classes(new_classes, str(classes_path))

    # 4. Concept 提取
    if verbose:
        print("\n" + "=" * 50)
        print("阶段 3: 生成 Concept 实体")
        print("=" * 50)

    concept_extractor = ConceptExtractor()

    # 准备知识点类型映射
    kps_with_types = []
    for kp, result in zip(knowledge_points, class_results):
        # 获取 class_id
        class_label = result.class_label
        class_id = None
        for cls in class_extractor.existing_classes:
            if cls["label"] == class_label:
                class_id = cls["id"]
                break
        if not class_id:
            # 新 Class，使用新生成的 ID
            for new_cls in new_classes:
                if new_cls["label"] == class_label:
                    class_id = new_cls["id"]
                    break
        if not class_id:
            class_id = "shuxuegainian-117c187fe4c4046bc9978c6d0d1c2504"  # 默认：数学概念

        kps_with_types.append({
            "knowledge_point": kp,
            "class_label": class_label,
            "class_id": class_id,
        })

    concepts = concept_extractor.extract_concepts_from_kps(kps_with_types, verbose=verbose)

    # 保存 concepts.json
    concepts_path = output_dir / "concepts.json"
    concept_extractor.save_concepts(concepts, str(concepts_path))

    # 5. Statement 提取
    if verbose:
        print("\n" + "=" * 50)
        print("阶段 4: 生成 Statement 定义（使用 LLM）")
        print("=" * 50)

    statement_extractor = StatementExtractor()
    statements = statement_extractor.extract_statements_from_concepts(concepts, verbose=verbose)

    # 保存 statements.json
    statements_path = output_dir / "statements.json"
    statement_extractor.save_statements(statements, str(statements_path))

    # 6. 关系提取
    if verbose:
        print("\n" + "=" * 50)
        print("阶段 5: 提取关系")
        print("=" * 50)

    relation_extractor = RelationExtractor()
    relations = relation_extractor.extract_all_relations(statements, concepts, verbose=verbose)

    # 保存 relations.json
    relations_path = output_dir / "relations.json"
    relation_extractor.save_relations(relations, str(relations_path))

    # 7. 输出统计
    elapsed = time.time() - start_time

    result = {
        "total_knowledge_points": len(knowledge_points),
        "new_classes": len(new_classes),
        "concepts": len(concepts),
        "statements": len(statements),
        "relations": len(relations),
        "elapsed_seconds": round(elapsed, 2),
        "output_files": {
            "classes": str(classes_path),
            "concepts": str(concepts_path),
            "statements": str(statements_path),
            "relations": str(relations_path),
        },
    }

    if verbose:
        print("\n" + "=" * 50)
        print("构建完成!")
        print("=" * 50)
        print(f"知识点数量: {result['total_knowledge_points']}")
        print(f"新增 Class: {result['new_classes']}")
        print(f"Concept: {result['concepts']}")
        print(f"Statement: {result['statements']}")
        print(f"Relation: {result['relations']}")
        print(f"耗时: {result['elapsed_seconds']} 秒")
        print("\n输出文件:")
        for name, path in result["output_files"].items():
            print(f"  - {name}: {path}")

    return result


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="知识图谱构建")
    parser.add_argument(
        "--ocr-result",
        default="edukg/data/eduBureau/math/ocr_result.json",
        help="OCR 结果 JSON 文件路径",
    )
    parser.add_argument(
        "--output-dir",
        default="edukg/data/eduBureau/math/",
        help="输出目录",
    )
    parser.add_argument(
        "--skip-extraction",
        action="store_true",
        help="跳过知识点提取，使用已有 curriculum_kps.json",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="调试模式",
    )

    args = parser.parse_args()

    # 检查文件存在
    if not Path(args.ocr_result).exists():
        print(f"错误: OCR 结果文件不存在: {args.ocr_result}")
        return 1

    # 验证配置
    if not settings.ZHIPU_API_KEY:
        print("警告: ZHIPU_API_KEY 未配置，将使用默认值")
        print("建议在 ai-edu-ai-service/.env 中配置 ZHIPU_API_KEY")

    # 构建
    result = build_knowledge_graph(
        ocr_result_path=args.ocr_result,
        output_dir=args.output_dir,
        skip_extraction=args.skip_extraction,
        verbose=True,
    )

    return 0


if __name__ == "__main__":
    exit(main())