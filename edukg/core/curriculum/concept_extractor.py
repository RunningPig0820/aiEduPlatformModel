"""
Concept 提取服务

从知识点列表生成 Concept 实体，添加 HAS_TYPE 关系，生成符合 Neo4j 导入格式的 concepts.json
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .kg_builder import URIGenerator, KGConfig


@dataclass
class ConceptExtractionResult:
    """Concept 提取结果"""
    knowledge_point: str
    concept_uri: str
    class_id: str


class ConceptExtractor:
    """
    Concept 提取器

    从知识点列表生成 Concept 实体，包括：
    1. 生成 Concept URI
    2. 添加 HAS_TYPE 关系（关联到 Class）
    3. 生成 concepts.json
    """

    def __init__(
        self,
        config: Optional[KGConfig] = None,
    ):
        """
        初始化 Concept 提取器

        Args:
            config: 知识图谱配置
        """
        self.config = config or KGConfig()
        self.uri_generator = URIGenerator(
            version=self.config.version,
            subject=self.config.subject,
        )

    def generate_concept(
        self,
        label: str,
        class_id: str,
        context: Optional[str] = None,
    ) -> dict:
        """
        生成单个 Concept 实体

        Args:
            label: 知识点名称
            class_id: 关联的 Class ID（不含 URI 前缀）
            context: 可选的上下文信息

        Returns:
            Concept 定义字典
        """
        uri = self.uri_generator.generate_instance_uri(label)

        return {
            "uri": uri,
            "label": label,
            "types": [class_id],
        }

    def batch_generate_concepts(
        self,
        knowledge_points: list[tuple[str, str]],
        verbose: bool = False,
    ) -> list[dict]:
        """
        批量生成 Concept 实体

        Args:
            knowledge_points: 知识点列表，每个元素是 (label, class_id) 元组
            verbose: 是否显示进度

        Returns:
            Concept 定义列表
        """
        concepts = []

        for i, (label, class_id) in enumerate(knowledge_points):
            if verbose and (i + 1) % 50 == 0:
                print(f"生成 Concept 进度: {i + 1}/{len(knowledge_points)}")

            concept = self.generate_concept(label, class_id)
            concepts.append(concept)

        return concepts

    def extract_concepts_from_kps(
        self,
        kps_with_types: list[dict],
        verbose: bool = False,
    ) -> list[dict]:
        """
        从知识点列表（带类型推断结果）提取 Concept

        Args:
            kps_with_types: 知识点列表，每个元素包含 knowledge_point, class_label, class_id
            verbose: 是否显示进度

        Returns:
            Concept 定义列表
        """
        # 转换为 (label, class_id) 元组列表
        kp_tuples = [
            (kp["knowledge_point"], kp["class_id"])
            for kp in kps_with_types
        ]

        return self.batch_generate_concepts(kp_tuples, verbose=verbose)

    def save_concepts(
        self,
        concepts: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 concepts.json

        Args:
            concepts: Concept 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(concepts, f, ensure_ascii=False, indent=2)

        print(f"Concepts 已保存到: {output_path} ({len(concepts)} 个)")


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Concept 提取")
    parser.add_argument("--kps", required=True, help="知识点 JSON 文件（带类型）")
    parser.add_argument("--output", default="concepts.json", help="输出文件")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    # 加载知识点
    with open(args.kps, encoding="utf-8") as f:
        kps_with_types = json.load(f)

    extractor = ConceptExtractor()
    concepts = extractor.extract_concepts_from_kps(kps_with_types, verbose=True)
    extractor.save_concepts(concepts, args.output)