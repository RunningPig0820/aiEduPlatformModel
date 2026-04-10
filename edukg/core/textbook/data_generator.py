"""
教材数据生成器

从原始 JSON 文件提取节点和关系数据，输出标准格式 JSON。
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from edukg.core.textbook.config import (
    DATA_DIR,
    OUTPUT_DIR,
    STAGE_CONFIG,
    OUTPUT_FILES,
)
from edukg.core.textbook.uri_generator import URIGenerator
from edukg.core.textbook.filters import is_valid_knowledge_point, filter_knowledge_points

logger = logging.getLogger(__name__)


class TextbookDataGenerator:
    """
    教材数据生成器

    从原始 JSON 文件提取节点和关系数据。

    使用方法:
        generator = TextbookDataGenerator()
        results = generator.generate_all()
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ):
        """
        初始化数据生成器

        Args:
            data_dir: 数据目录路径（默认使用配置）
            output_dir: 输出目录路径（默认使用配置）
        """
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.uri_generator = URIGenerator()

        # 统计信息
        self.stats = {
            "textbooks": 0,
            "chapters": 0,
            "sections": 0,
            "textbook_kps": 0,
            "contains_relations": 0,
            "in_unit_relations": 0,
        }

        # 缓存
        self._textbooks: List[Dict] = []
        self._chapters: List[Dict] = []
        self._sections: List[Dict] = []
        self._textbook_kps: List[Dict] = []
        self._contains_relations: List[Dict] = []
        self._in_unit_relations: List[Dict] = []

        # 知识点序号计数器
        self._kp_seq = 0

    def discover_files(self) -> List[Path]:
        """
        发现教材 JSON 文件

        Returns:
            JSON 文件路径列表
        """
        files = []

        # 小学: primary/grade1-6/shang.json, xia.json
        primary_dir = self.data_dir / "primary"
        if primary_dir.exists():
            for grade_dir in sorted(primary_dir.glob("grade*")):
                for sem_file in ["shang.json", "xia.json"]:
                    filepath = grade_dir / sem_file
                    if filepath.exists():
                        files.append(filepath)

        # 初中: middle/grade7-9/shang.json, xia.json
        middle_dir = self.data_dir / "middle"
        if middle_dir.exists():
            for grade_dir in sorted(middle_dir.glob("grade*")):
                for sem_file in ["shang.json", "xia.json"]:
                    filepath = grade_dir / sem_file
                    if filepath.exists():
                        files.append(filepath)

        # 高中: high/bixiu1-3/textbook.json
        high_dir = self.data_dir / "high"
        if high_dir.exists():
            for bixiu_dir in sorted(high_dir.glob("bixiu*")):
                filepath = bixiu_dir / "textbook.json"
                if filepath.exists():
                    files.append(filepath)

        logger.info(f"发现 {len(files)} 个教材 JSON 文件")
        return files

    def _load_json(self, filepath: Path) -> Dict:
        """加载 JSON 文件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _parse_textbook(self, data: Dict) -> Dict:
        """
        解析教材元数据，生成教材节点

        Args:
            data: JSON 数据

        Returns:
            教材节点字典
        """
        stage = data.get("stage", "")
        grade = data.get("grade", "")
        semester = data.get("semester", "")
        publisher = data.get("publisher", "")

        # 生成 ID
        tb_id = self.uri_generator.textbook_id(publisher, grade, semester)
        tb_uri = self.uri_generator.textbook_uri(tb_id)

        # 学段名称
        stage_name = STAGE_CONFIG.get(stage, {}).get("name", stage)

        return {
            "uri": tb_uri,
            "id": tb_id,
            "label": f"{stage_name}{grade}" + (f"{semester}" if semester and semester != "未知学期" else ""),
            "stage": stage_name,
            "grade": grade,
            "semester": semester if semester and semester != "未知学期" else "",
            "publisher": publisher,
            "edition": data.get("edition", ""),
            "source_url": data.get("source_url", ""),
        }

    def _parse_chapters(self, data: Dict, tb_id: str) -> List[Dict]:
        """
        解析章节数据

        Args:
            data: JSON 数据
            tb_id: 教材 ID

        Returns:
            章节节点列表
        """
        chapters = []
        for ch in data.get("chapters", []):
            ch_order = ch.get("chapter_order", 0)
            ch_name = ch.get("chapter_name", "")

            ch_id = self.uri_generator.chapter_id(tb_id, ch_order)
            ch_uri = self.uri_generator.chapter_uri(ch_id)

            chapters.append({
                "uri": ch_uri,
                "id": ch_id,
                "label": ch_name,
                "order": ch_order,
                "textbook_id": tb_id,
            })

        return chapters

    def _parse_sections(
        self,
        data: Dict,
        tb_id: str,
        chapters: List[Dict],
        stage: str
    ) -> tuple:
        """
        解析小节数据

        Args:
            data: JSON 数据
            tb_id: 教材 ID
            chapters: 章节节点列表
            stage: 学段

        Returns:
            (sections, textbook_kps, contains_relations, in_unit_relations)
        """
        sections = []
        textbook_kps = []
        contains_relations = []
        in_unit_relations = []

        for ch in data.get("chapters", []):
            ch_order = ch.get("chapter_order", 0)
            ch_id = self.uri_generator.chapter_id(tb_id, ch_order)

            for sec in ch.get("sections", []):
                sec_order = sec.get("section_order", 0)
                sec_name = sec.get("section_name", "")
                kps = sec.get("knowledge_points", [])

                sec_id = self.uri_generator.section_id(ch_id, sec_order)
                sec_uri = self.uri_generator.section_uri(sec_id)

                sections.append({
                    "uri": sec_uri,
                    "id": sec_id,
                    "label": sec_name,
                    "order": sec_order,
                    "chapter_id": ch_id,
                    "textbook_id": tb_id,
                })

                # 处理知识点
                valid_kps = filter_knowledge_points(kps)
                for kp_name in valid_kps:
                    self._kp_seq += 1
                    kp_uri = self.uri_generator.textbookkp_uri(stage, self._kp_seq)

                    # 获取年级信息
                    grade = data.get("grade", "")
                    stage_name = STAGE_CONFIG.get(stage, {}).get("name", "")

                    textbook_kps.append({
                        "uri": kp_uri,
                        "label": kp_name,
                        "stage": stage_name,
                        "grade": grade,
                        "section_id": sec_id,
                        "textbook_id": tb_id,
                    })

                    # IN_UNIT 关系
                    in_unit_relations.append({
                        "kp_uri": kp_uri,
                        "section_id": sec_id,
                        "textbook_id": tb_id,
                    })

        return sections, textbook_kps, contains_relations, in_unit_relations

    def generate_textbooks(self) -> List[Dict]:
        """生成教材节点数据"""
        if self._textbooks:
            return self._textbooks

        files = self.discover_files()
        for filepath in files:
            data = self._load_json(filepath)
            tb = self._parse_textbook(data)
            self._textbooks.append(tb)

        self.stats["textbooks"] = len(self._textbooks)
        logger.info(f"生成 {len(self._textbooks)} 个教材节点")
        return self._textbooks

    def generate_chapters(self) -> List[Dict]:
        """生成章节节点数据"""
        if self._chapters:
            return self._chapters

        files = self.discover_files()
        for filepath in files:
            data = self._load_json(filepath)
            tb = self._parse_textbook(data)
            chapters = self._parse_chapters(data, tb["id"])
            self._chapters.extend(chapters)

        self.stats["chapters"] = len(self._chapters)
        logger.info(f"生成 {len(self._chapters)} 个章节节点")
        return self._chapters

    def generate_sections(self) -> List[Dict]:
        """生成小节节点数据"""
        if self._sections:
            return self._sections

        self._generate_all_data()
        return self._sections

    def generate_textbook_kps(self) -> List[Dict]:
        """生成教材知识点节点数据"""
        if self._textbook_kps:
            return self._textbook_kps

        self._generate_all_data()
        return self._textbook_kps

    def generate_relations(self) -> Dict[str, List[Dict]]:
        """生成关系数据"""
        if self._contains_relations or self._in_unit_relations:
            return {
                "contains": self._contains_relations,
                "in_unit": self._in_unit_relations,
            }

        self._generate_all_data()
        return {
            "contains": self._contains_relations,
            "in_unit": self._in_unit_relations,
        }

    def _generate_all_data(self):
        """生成所有数据（内部方法）"""
        if self._textbooks:  # 已经生成过
            return

        files = self.discover_files()
        for filepath in files:
            data = self._load_json(filepath)
            stage = data.get("stage", "")

            # 教材
            tb = self._parse_textbook(data)
            self._textbooks.append(tb)

            # 章节
            chapters = self._parse_chapters(data, tb["id"])
            self._chapters.extend(chapters)

            # 小节和知识点
            sections, kps, _, in_unit = self._parse_sections(
                data, tb["id"], chapters, stage
            )
            self._sections.extend(sections)
            self._textbook_kps.extend(kps)
            self._in_unit_relations.extend(in_unit)

        # 生成 CONTAINS 关系
        self._generate_contains_relations()

        # 更新统计
        self.stats["textbooks"] = len(self._textbooks)
        self.stats["chapters"] = len(self._chapters)
        self.stats["sections"] = len(self._sections)
        self.stats["textbook_kps"] = len(self._textbook_kps)
        self.stats["in_unit_relations"] = len(self._in_unit_relations)
        self.stats["contains_relations"] = len(self._contains_relations)

    def _generate_contains_relations(self):
        """生成 CONTAINS 关系"""
        # Textbook → Chapter
        for ch in self._chapters:
            self._contains_relations.append({
                "from_id": ch["textbook_id"],
                "from_type": "Textbook",
                "to_id": ch["id"],
                "to_type": "Chapter",
                "relation_type": "CONTAINS",
            })

        # Chapter → Section
        for sec in self._sections:
            self._contains_relations.append({
                "from_id": sec["chapter_id"],
                "from_type": "Chapter",
                "to_id": sec["id"],
                "to_type": "Section",
                "relation_type": "CONTAINS",
            })

    def generate_all(self) -> Dict[str, str]:
        """
        生成所有数据文件

        Returns:
            {'textbooks': 'path/to/textbooks.json', ...}
        """
        # 生成数据
        self._generate_all_data()

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        output_paths = {}

        for key, filename in OUTPUT_FILES.items():
            if key == "import_summary":
                continue

            filepath = self.output_dir / filename

            if key == "textbooks":
                data = self._textbooks
            elif key == "chapters":
                data = self._chapters
            elif key == "sections":
                data = self._sections
            elif key == "textbook_kps":
                data = self._textbook_kps
            elif key == "contains_relations":
                data = self._contains_relations
            elif key == "in_unit_relations":
                data = self._in_unit_relations
            else:
                continue

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            output_paths[key] = str(filepath)
            logger.info(f"保存: {filepath} ({len(data)} 条)")

        # 保存统计摘要
        summary_path = self.output_dir / OUTPUT_FILES["import_summary"]
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        output_paths["import_summary"] = str(summary_path)

        logger.info(f"\n=== 数据生成完成 ===")
        for key, count in self.stats.items():
            logger.info(f"  {key}: {count}")

        return output_paths

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.stats.copy()