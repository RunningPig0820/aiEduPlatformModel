"""
教材数据处理模块单元测试

测试 URI 生成、知识点过滤、数据解析逻辑。
"""
import pytest
from pathlib import Path

from edukg.core.textbook import (
    URIGenerator,
    TextbookDataGenerator,
    is_valid_knowledge_point,
    filter_knowledge_points,
    NON_KNOWLEDGE_POINT_MARKERS,
)


class TestURIGenerator:
    """URI 生成器测试"""

    def setup_method(self):
        self.generator = URIGenerator()

    def test_textbook_id_primary(self):
        """测试小学教材 ID 生成"""
        # 一年级上册
        tb_id = self.generator.textbook_id("人民教育出版社", "一年级", "上册")
        assert tb_id == "renjiao-g1s"

        # 六年级下册
        tb_id = self.generator.textbook_id("人民教育出版社", "六年级", "下册")
        assert tb_id == "renjiao-g6x"

    def test_textbook_id_middle(self):
        """测试初中教材 ID 生成"""
        # 七年级上册
        tb_id = self.generator.textbook_id("人民教育出版社", "七年级", "上册")
        assert tb_id == "renjiao-g7s"

        # 九年级下册
        tb_id = self.generator.textbook_id("人民教育出版社", "九年级", "下册")
        assert tb_id == "renjiao-g9x"

    def test_textbook_id_high(self):
        """测试高中教材 ID 生成"""
        # 必修第一册（高中无学期）
        tb_id = self.generator.textbook_id("人民教育出版社", "必修第一册")
        assert tb_id == "renjiao-bixiu1"

        # 必修第三册
        tb_id = self.generator.textbook_id("人民教育出版社", "必修第三册")
        assert tb_id == "renjiao-bixiu3"

    def test_chapter_id(self):
        """测试章节 ID 生成"""
        ch_id = self.generator.chapter_id("renjiao-g1s", 1)
        assert ch_id == "renjiao-g1s-1"

        ch_id = self.generator.chapter_id("renjiao-g7x", 5)
        assert ch_id == "renjiao-g7x-5"

    def test_section_id(self):
        """测试小节 ID 生成"""
        sec_id = self.generator.section_id("renjiao-g1s-1", 1)
        assert sec_id == "renjiao-g1s-1-1"

        sec_id = self.generator.section_id("renjiao-g7x-3", 2)
        assert sec_id == "renjiao-g7x-3-2"

    def test_textbook_uri(self):
        """测试教材 URI 生成"""
        uri = self.generator.textbook_uri("renjiao-g1s")
        assert uri == "http://edukg.org/knowledge/3.1/textbook/math#renjiao-g1s"

    def test_chapter_uri(self):
        """测试章节 URI 生成"""
        uri = self.generator.chapter_uri("renjiao-g1s-1")
        assert uri == "http://edukg.org/knowledge/3.1/chapter/math#renjiao-g1s-1"

    def test_section_uri(self):
        """测试小节 URI 生成"""
        uri = self.generator.section_uri("renjiao-g1s-1-1")
        assert uri == "http://edukg.org/knowledge/3.1/section/math#renjiao-g1s-1-1"

    def test_textbookkp_uri(self):
        """测试知识点 URI 生成"""
        uri = self.generator.textbookkp_uri("primary", 1)
        assert uri == "http://edukg.org/knowledge/3.1/instance/math#textbook-primary-00001"

        uri = self.generator.textbookkp_uri("middle", 100)
        assert uri == "http://edukg.org/knowledge/3.1/instance/math#textbook-middle-00100"

    def test_encode_grade(self):
        """测试年级编码"""
        assert self.generator.encode_grade("一年级") == "g1"
        assert self.generator.encode_grade("七年级") == "g7"
        assert self.generator.encode_grade("必修第一册") == "bixiu1"

    def test_encode_semester(self):
        """测试学期编码"""
        assert self.generator.encode_semester("上册") == "s"
        assert self.generator.encode_semester("下册") == "x"
        assert self.generator.encode_semester("未知学期") == ""

    def test_parse_textbook_id(self):
        """测试教材 ID 解析"""
        result = self.generator.parse_textbook_id("renjiao-g1s")
        assert result["publisher_code"] == "renjiao"
        assert result["grade_code"] == "g1"
        assert result["semester_code"] == "s"

        result = self.generator.parse_textbook_id("renjiao-bixiu1")
        assert result["publisher_code"] == "renjiao"
        assert result["grade_code"] == "bixiu1"
        assert result["semester_code"] == ""


class TestKnowledgePointFilter:
    """知识点过滤测试"""

    def test_valid_knowledge_point(self):
        """测试有效知识点"""
        assert is_valid_knowledge_point("加法") == True
        assert is_valid_knowledge_point("正数和负数的概念") == True
        assert is_valid_knowledge_point("一元二次方程") == True

    def test_invalid_knowledge_point_markers(self):
        """测试非知识点标记"""
        for marker in NON_KNOWLEDGE_POINT_MARKERS:
            assert is_valid_knowledge_point(marker) == False

    def test_invalid_knowledge_point_prefix(self):
        """测试前缀过滤"""
        assert is_valid_knowledge_point("复习题一") == False
        assert is_valid_knowledge_point("复习题") == False

    def test_invalid_knowledge_point_chapter_number(self):
        """测试章节编号过滤"""
        assert is_valid_knowledge_point("1.1") == False
        assert is_valid_knowledge_point("1.2.3") == False
        assert is_valid_knowledge_point("123") == False

    def test_empty_knowledge_point(self):
        """测试空知识点"""
        assert is_valid_knowledge_point("") == False
        assert is_valid_knowledge_point("  ") == False
        assert is_valid_knowledge_point(None) == False

    def test_filter_knowledge_points(self):
        """测试批量过滤"""
        kps = ["加法", "减法", "数学活动", "小结", "一元二次方程"]
        filtered = filter_knowledge_points(kps)
        assert filtered == ["加法", "减法", "一元二次方程"]


class TestTextbookDataGenerator:
    """数据生成器测试"""

    def test_init(self):
        """测试初始化"""
        generator = TextbookDataGenerator()
        assert generator.data_dir is not None
        assert generator.output_dir is not None

    def test_discover_files(self):
        """测试文件发现"""
        generator = TextbookDataGenerator()
        files = generator.discover_files()

        # 应该发现 21 个文件（小学 12 + 初中 6 + 高中 3）
        assert len(files) == 21

        # 检查文件名
        file_names = [f.name for f in files]
        assert "shang.json" in file_names
        assert "xia.json" in file_names
        assert "textbook.json" in file_names


# 运行测试的命令
if __name__ == '__main__':
    pytest.main([__file__, '-v'])