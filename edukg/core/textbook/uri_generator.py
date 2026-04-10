"""
URI 生成器

用于生成教材、章节、小节、知识点的 URI 和 ID。
版本: v3.1
"""
from typing import Optional
from edukg.core.textbook.config import (
    URI_PREFIX,
    URI_VERSION,
    GRADE_ENCODING,
    SEMESTER_ENCODING,
    PUBLISHER_ENCODING,
)


class URIGenerator:
    """
    URI 生成器

    用于生成教材数据的 URI 和 ID。

    使用方法:
        generator = URIGenerator()
        tb_id = generator.textbook_id("人民教育出版社", "一年级", "上册")
        # 返回: "renjiao-g1s"

        ch_id = generator.chapter_id(tb_id, 1)
        # 返回: "renjiao-g1s-1"
    """

    def __init__(self, subject: str = "math"):
        """
        初始化 URI 生成器

        Args:
            subject: 学科标识（默认: math）
        """
        self.subject = subject
        self.uri_prefix = URI_PREFIX
        self.uri_version = URI_VERSION

    # ============ ID 生成方法 ============

    def textbook_id(
        self,
        publisher: str,
        grade: str,
        semester: Optional[str] = None
    ) -> str:
        """
        生成教材 ID

        Args:
            publisher: 出版社名称
            grade: 年级名称
            semester: 学期名称（高中可省略）

        Returns:
            教材 ID，如 "renjiao-g1s"

        Examples:
            >>> generator.textbook_id("人民教育出版社", "一年级", "上册")
            'renjiao-g1s'
            >>> generator.textbook_id("人民教育出版社", "七年级", "下册")
            'renjiao-g7x'
            >>> generator.textbook_id("人民教育出版社", "必修第一册")
            'renjiao-bixiu1'
        """
        # 出版社编码
        pub_code = PUBLISHER_ENCODING.get(publisher, publisher)

        # 年级编码
        grade_code = GRADE_ENCODING.get(grade, grade)

        # 学期编码（高中无学期）
        sem_code = ""
        if semester and semester in SEMESTER_ENCODING:
            sem_code = SEMESTER_ENCODING[semester]

        return f"{pub_code}-{grade_code}{sem_code}"

    def chapter_id(self, textbook_id: str, order: int) -> str:
        """
        生成章节 ID

        Args:
            textbook_id: 教材 ID
            order: 章节顺序号

        Returns:
            章节 ID，如 "renjiao-g1s-1"
        """
        return f"{textbook_id}-{order}"

    def section_id(self, chapter_id: str, order: int) -> str:
        """
        生成小节 ID

        Args:
            chapter_id: 章节 ID
            order: 小节顺序号

        Returns:
            小节 ID，如 "renjiao-g1s-1-1"
        """
        return f"{chapter_id}-{order}"

    # ============ URI 生成方法 ============

    def textbook_uri(self, textbook_id: str) -> str:
        """
        生成教材 URI

        Args:
            textbook_id: 教材 ID

        Returns:
            教材 URI，如 "http://edukg.org/knowledge/3.1/textbook/math#renjiao-g1s"
        """
        return f"{self.uri_prefix}/textbook/{self.subject}#{textbook_id}"

    def chapter_uri(self, chapter_id: str) -> str:
        """
        生成章节 URI

        Args:
            chapter_id: 章节 ID

        Returns:
            章节 URI，如 "http://edukg.org/knowledge/3.1/chapter/math#renjiao-g1s-1"
        """
        return f"{self.uri_prefix}/chapter/{self.subject}#{chapter_id}"

    def section_uri(self, section_id: str) -> str:
        """
        生成小节 URI

        Args:
            section_id: 小节 ID

        Returns:
            小节 URI，如 "http://edukg.org/knowledge/3.1/section/math#renjiao-g1s-1-1"
        """
        return f"{self.uri_prefix}/section/{self.subject}#{section_id}"

    def textbookkp_uri(self, stage: str, seq: int) -> str:
        """
        生成教材知识点 URI

        Args:
            stage: 学段标识（primary/middle/high）
            seq: 序号

        Returns:
            知识点 URI，如 "http://edukg.org/knowledge/3.1/instance/math#textbook-primary-00001"
        """
        stage_name = {"primary": "primary", "middle": "middle", "high": "high"}.get(stage, stage)
        return f"{self.uri_prefix}/instance/{self.subject}#textbook-{stage_name}-{seq:05d}"

    # ============ 编码转换方法 ============

    @staticmethod
    def encode_grade(grade: str) -> str:
        """
        年级名称转编码

        Args:
            grade: 年级名称

        Returns:
            年级编码
        """
        return GRADE_ENCODING.get(grade, grade)

    @staticmethod
    def encode_semester(semester: str) -> str:
        """
        学期名称转编码

        Args:
            semester: 学期名称

        Returns:
            学期编码
        """
        return SEMESTER_ENCODING.get(semester, "")

    @staticmethod
    def encode_publisher(publisher: str) -> str:
        """
        出版社名称转编码

        Args:
            publisher: 出版社名称

        Returns:
            出版社编码
        """
        return PUBLISHER_ENCODING.get(publisher, publisher)

    # ============ 反向解析方法 ============

    def parse_textbook_id(self, textbook_id: str) -> dict:
        """
        解析教材 ID

        Args:
            textbook_id: 教材 ID，如 "renjiao-g1s"

        Returns:
            解析结果字典，包含 publisher_code, grade_code, semester_code
        """
        parts = textbook_id.split("-")
        if len(parts) < 2:
            return {"error": "Invalid textbook ID format"}

        publisher_code = parts[0]
        grade_sem = parts[1]

        # 解析年级和学期
        # 格式: g1s, g7x, bixiu1
        grade_code = grade_sem
        semester_code = ""

        # 检查是否有学期后缀
        for sem_name, sem_code in SEMESTER_ENCODING.items():
            if grade_sem.endswith(sem_code):
                grade_code = grade_sem[:-1]
                semester_code = sem_code
                break

        return {
            "publisher_code": publisher_code,
            "grade_code": grade_code,
            "semester_code": semester_code,
            "textbook_id": textbook_id
        }