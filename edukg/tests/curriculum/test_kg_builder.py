"""
知识图谱构建服务测试

测试 KGBuilder 和 URIGenerator
"""
import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from edukg.core.curriculum.kg_builder import (
    KGBuilder,
    URIGenerator,
    KGConfig,
)


class TestURIGenerator:
    """URI 生成器测试"""

    def test_generate_class_uri(self):
        """测试生成 Class URI"""
        generator = URIGenerator()

        label = "小学数概念"
        uri = generator.generate_class_uri(label)

        # 验证 URI 格式
        assert uri.startswith("http://edukg.org/knowledge/0.2/class/math#")

        # 验证 ID 格式: {pinyin}-{md5}
        id_part = uri.split("#")[1]
        assert id_part.startswith("xiaoxueshugainian-")

        # 验证 MD5 部分
        expected_md5 = hashlib.md5(label.encode("utf-8")).hexdigest()
        assert expected_md5 in id_part

    def test_generate_instance_uri(self):
        """测试生成 Concept URI (instance)"""
        generator = URIGenerator()

        label = "凑十法"
        uri = generator.generate_instance_uri(label)

        # 验证 URI 格式
        assert uri.startswith("http://edukg.org/knowledge/0.2/instance/math#")

        # 验证 ID 格式: {pinyin}-{md5}
        id_part = uri.split("#")[1]
        # pypinyin 将 "凑十法" 转为 "coushifa"
        assert id_part.startswith("coushifa-")

    def test_generate_statement_uri(self):
        """测试生成 Statement URI"""
        generator = URIGenerator()

        label = "凑十法的定义"
        uri = generator.generate_statement_uri(label)

        # 验证 URI 格式
        assert uri.startswith("http://edukg.org/knowledge/0.2/statement/math#")

        # 验证 ID 格式: {pinyin}-{md5}
        id_part = uri.split("#")[1]
        # pypinyin 将 "凑十法的定义" 转为 "coushifadedingyi"
        assert "coushifa" in id_part

    def test_generate_id_format(self):
        """测试 ID 生成格式"""
        generator = URIGenerator()

        label = "有理数"
        id_str = generator.generate_id(label)

        # 验证格式: {pinyin}-{md5}
        expected_pinyin = "youlishu"
        expected_md5 = hashlib.md5(label.encode("utf-8")).hexdigest()

        assert id_str == f"{expected_pinyin}-{expected_md5}"

    def test_generate_uri_consistent(self):
        """测试同一标签生成 URI 一致"""
        generator = URIGenerator()

        label = "一元一次方程"
        uri1 = generator.generate_instance_uri(label)
        uri2 = generator.generate_instance_uri(label)

        assert uri1 == uri2

    def test_pinyin_conversion(self):
        """测试拼音转换"""
        generator = URIGenerator()

        # 测试简单汉字
        assert generator._to_pinyin("数") == "shu"
        assert generator._to_pinyin("学") == "xue"
        assert generator._to_pinyin("概念") == "gainian"

        # 测试长字符串
        assert generator._to_pinyin("小学数概念") == "xiaoxueshugainian"

    def test_custom_subject(self):
        """测试自定义学科"""
        generator = URIGenerator(subject="physics")

        uri = generator.generate_class_uri("物理概念")
        assert "physics" in uri


class TestKGBuilder:
    """知识图谱构建器测试"""

    def test_init_default_config(self):
        """测试默认配置初始化"""
        builder = KGBuilder()

        assert builder.config.version == "0.2"
        assert builder.config.subject == "math"

    def test_init_custom_config(self):
        """测试自定义配置"""
        config = KGConfig(
            version="0.3",
            subject="physics",
            output_dir=Path("/tmp/test"),
        )
        builder = KGBuilder(config=config)

        assert builder.config.version == "0.3"
        assert builder.config.subject == "physics"

    def test_build_from_ocr_result(self, tmp_path):
        """测试从 OCR 结果构建知识图谱"""
        # 创建测试 OCR 结果
        ocr_data = {
            "pdf_path": "test.pdf",
            "total_pages": 3,
            "pages": [
                {"page_num": 1, "text": "第一学段（1-2年级）数与代数：20以内数的认识、加减法"},
                {"page_num": 2, "text": "凑十法是一种计算方法"},
            ]
        }

        ocr_path = tmp_path / "ocr_result.json"
        with open(ocr_path, "w", encoding="utf-8") as f:
            json.dump(ocr_data, f)

        # 构建知识图谱
        config = KGConfig(output_dir=tmp_path)
        builder = KGBuilder(config=config)

        # 注意: 这里不实际调用 LLM，只是测试框架结构
        # 实际测试需要 Mock LLM

    def test_save_classes(self, tmp_path):
        """测试保存 classes.json"""
        builder = KGBuilder()

        # 创建测试 Class 数据
        classes = [
            {
                "uri": "http://edukg.org/knowledge/0.2/class/math#test-abc123",
                "id": "test-abc123",
                "subject": "math",
                "label": "测试概念",
                "description": "测试概念",
                "parents": ["http://edukg.org/knowledge/0.1/class/math#shuxuegainian-xxx"],
                "type": "owl:Class",
            }
        ]

        output_path = tmp_path / "classes.json"
        builder.save_classes(classes, str(output_path))

        # 验证文件存在
        assert output_path.exists()

        # 验证内容
        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert data["subject"] == "math"
        assert data["class_count"] == 1
        assert len(data["classes"]) == 1

    def test_save_concepts(self, tmp_path):
        """测试保存 concepts.json"""
        builder = KGBuilder()

        concepts = [
            {
                "uri": "http://edukg.org/knowledge/0.2/instance/math#coutishufa-abc123",
                "label": "凑十法",
                "types": ["shuxuefangfa-xxx"],
            }
        ]

        output_path = tmp_path / "concepts.json"
        builder.save_concepts(concepts, str(output_path))

        assert output_path.exists()

    def test_save_statements(self, tmp_path):
        """测试保存 statements.json"""
        builder = KGBuilder()

        statements = [
            {
                "uri": "http://edukg.org/knowledge/0.2/statement/math#coutishufa-abc123",
                "label": "凑十法的定义",
                "types": ["shuxuedingyi-xxx"],
                "content": "凑十法是一种计算方法...",
            }
        ]

        output_path = tmp_path / "statements.json"
        builder.save_statements(statements, str(output_path))

        assert output_path.exists()

    def test_save_relations(self, tmp_path):
        """测试保存 relations.json"""
        builder = KGBuilder()

        relations = [
            {
                "from": {
                    "uri": "http://edukg.org/knowledge/0.2/statement/math#xxx",
                    "label": "凑十法的定义",
                },
                "relation": "relatedTo",
                "to": {
                    "uri": "http://edukg.org/knowledge/0.2/instance/math#yyy",
                    "label": "凑十法",
                },
            }
        ]

        output_path = tmp_path / "relations.json"
        builder.save_relations(relations, str(output_path))

        assert output_path.exists()

        with open(output_path, encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "relations" in data


class TestKGConfig:
    """配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = KGConfig()

        assert config.version == "0.2"
        assert config.subject == "math"

    def test_custom_config(self):
        """测试自定义配置"""
        config = KGConfig(
            version="0.3",
            subject="chemistry",
        )

        assert config.version == "0.3"
        assert config.subject == "chemistry"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])