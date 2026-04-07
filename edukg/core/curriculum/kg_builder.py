"""
知识图谱构建服务

从课标知识点构建完整的知识图谱结构，输出符合 Neo4j 导入格式的 JSON 文件

URI 命名规范:
- 版本号: 0.2 (区分 EduKG 的 0.1)
- ID 格式: {label_pinyin}-{md5_32bit}
- MD5生成: hashlib.md5(label.encode("utf-8")).hexdigest()
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from pypinyin import lazy_pinyin

from .config import settings


@dataclass
class KGConfig:
    """知识图谱构建配置"""
    version: str = "0.2"  # 区分 EduKG 的 0.1
    subject: str = "math"
    output_dir: Path = Path(__file__).parent.parent.parent / "data" / "eduBureau" / "math"


class URIGenerator:
    """
    URI 生成器

    生成符合规范的 URI，用于知识图谱节点标识

    URI 格式: http://edukg.org/knowledge/{version}/{type}/{subject}#{id}
    ID 格式: {pinyin(label)}-{md5(label)}
    """

    def __init__(
        self,
        version: str = "0.2",
        subject: str = "math",
    ):
        """
        初始化 URI 生成器

        Args:
            version: 版本号，默认 0.2
            subject: 学科，默认 math
        """
        self.version = version
        self.subject = subject
        self.base_uri = f"http://edukg.org/knowledge/{version}"

    def _to_pinyin(self, label: str) -> str:
        """
        将中文标签转换为拼音

        Args:
            label: 中文标签

        Returns:
            拼音字符串（无分隔符）
        """
        # 使用 pypinyin 库转换
        pinyin_list = lazy_pinyin(label)
        return "".join(pinyin_list)

    def generate_id(self, label: str) -> str:
        """
        生成 ID

        格式: {pinyin}-{md5}

        Args:
            label: 标签

        Returns:
            ID 字符串
        """
        pinyin = self._to_pinyin(label)
        md5_hash = hashlib.md5(label.encode("utf-8")).hexdigest()
        return f"{pinyin}-{md5_hash}"

    def generate_class_uri(self, label: str) -> str:
        """
        生成 Class URI

        Args:
            label: Class 标签

        Returns:
            URI 字符串
        """
        id_str = self.generate_id(label)
        return f"{self.base_uri}/class/{self.subject}#{id_str}"

    def generate_instance_uri(self, label: str) -> str:
        """
        生成 Concept URI (instance 类型)

        Args:
            label: Concept 标签

        Returns:
            URI 字符串
        """
        id_str = self.generate_id(label)
        return f"{self.base_uri}/instance/{self.subject}#{id_str}"

    def generate_statement_uri(self, label: str) -> str:
        """
        生成 Statement URI

        Args:
            label: Statement 标签

        Returns:
            URI 字符串
        """
        id_str = self.generate_id(label)
        return f"{self.base_uri}/statement/{self.subject}#{id_str}"

    def generate_uri(self, label: str, uri_type: str) -> str:
        """
        通用 URI 生成方法

        Args:
            label: 标签
            uri_type: URI 类型 (class, instance, statement)

        Returns:
            URI 字符串
        """
        if uri_type == "class":
            return self.generate_class_uri(label)
        elif uri_type == "instance":
            return self.generate_instance_uri(label)
        elif uri_type == "statement":
            return self.generate_statement_uri(label)
        else:
            raise ValueError(f"不支持的 URI 类型: {uri_type}")


class KGBuilder:
    """
    知识图谱构建器

    从课标知识点构建完整的知识图谱结构，包括:
    - Class: 概念类
    - Concept: 知识点 (instance)
    - Statement: 定义描述
    - Relation: 关系

    输出符合 Neo4j 导入格式的独立 JSON 文件
    """

    def __init__(
        self,
        config: Optional[KGConfig] = None,
    ):
        """
        初始化知识图谱构建器

        Args:
            config: 配置，默认使用 KGConfig 默认值
        """
        self.config = config or KGConfig()
        self.uri_generator = URIGenerator(
            version=self.config.version,
            subject=self.config.subject,
        )

        # 存储构建过程中的数据
        self._classes: list[dict] = []
        self._concepts: list[dict] = []
        self._statements: list[dict] = []
        self._relations: list[dict] = []

    def build_from_ocr_result(
        self,
        ocr_result_path: str,
        verbose: bool = True,
    ) -> dict:
        """
        从 OCR 结果构建知识图谱

        这是一个完整流程，包括:
        1. 提取知识点 (使用 LLMExtractor)
        2. 推断 Class 类型 (使用 ClassExtractor)
        3. 生成 Concept 实体
        4. 生成 Statement 定义
        5. 提取关系

        Args:
            ocr_result_path: OCR 结果 JSON 文件路径
            verbose: 是否显示进度

        Returns:
            构建结果统计
        """
        # 注意: 这个方法将在后续任务中完整实现
        # 目前只是框架
        raise NotImplementedError("完整构建流程将在后续任务中实现")

    def save_classes(
        self,
        classes: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 classes.json

        格式符合 Neo4j 导入要求

        Args:
            classes: Class 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "subject": self.config.subject,
            "subject_name": self._get_subject_name(),
            "class_count": len(classes),
            "classes": classes,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Classes 已保存到: {output_path} ({len(classes)} 个)")

    def save_concepts(
        self,
        concepts: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 concepts.json

        格式符合 Neo4j 导入要求

        Args:
            concepts: Concept 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(concepts, f, ensure_ascii=False, indent=2)

        print(f"Concepts 已保存到: {output_path} ({len(concepts)} 个)")

    def save_statements(
        self,
        statements: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 statements.json

        格式符合 Neo4j 导入要求

        Args:
            statements: Statement 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(statements, f, ensure_ascii=False, indent=2)

        print(f"Statements 已保存到: {output_path} ({len(statements)} 个)")

    def save_relations(
        self,
        relations: list[dict],
        output_path: str,
    ) -> None:
        """
        保存 relations.json

        格式符合 Neo4j 导入要求

        Args:
            relations: Relation 列表
            output_path: 输出文件路径
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "metadata": {
                "total_relations": len(relations),
                "description": f"{self._get_subject_name()}知识点关联关系",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            "relations": relations,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Relations 已保存到: {output_path} ({len(relations)} 个)")

    def _get_subject_name(self) -> str:
        """获取学科中文名"""
        subject_names = {
            "math": "数学",
            "physics": "物理",
            "chemistry": "化学",
        }
        return subject_names.get(self.config.subject, self.config.subject)

    def get_output_files(self) -> dict[str, Path]:
        """
        获取输出文件路径

        Returns:
            文件名到路径的映射
        """
        output_dir = self.config.output_dir
        return {
            "classes": output_dir / "classes.json",
            "concepts": output_dir / "concepts.json",
            "statements": output_dir / "statements.json",
            "relations": output_dir / "relations.json",
        }


# 命令行入口
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="知识图谱构建")
    parser.add_argument("--ocr-result", required=True, help="OCR 结果 JSON 文件路径")
    parser.add_argument("--output-dir", default="edukg/data/eduBureau/math/", help="输出目录")
    parser.add_argument("--debug", action="store_true", help="调试模式")

    args = parser.parse_args()

    config = KGConfig(output_dir=Path(args.output_dir))
    builder = KGBuilder(config=config)

    # 构建知识图谱
    builder.build_from_ocr_result(args.ocr_result, verbose=True)