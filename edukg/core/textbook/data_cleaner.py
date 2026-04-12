"""
数据清洗器

清理冗余标签、规范 Section 名称格式。
根据 fanan.md 建议改进：
1. Section 序号保留到 order_in_book 字段，而不是删除
2. 检查"通用"标签的包含/被包含关系
3. 扩展清洗规则（全角/半角、空格等）
"""
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import Counter

logger = logging.getLogger(__name__)


class DataCleaner:
    """
    数据清洗器

    功能:
    1. 检测并处理"通用"标签的重复数据（检查包含关系）
    2. 清洗 Section 标签（序号保留到 order_in_book，清洗不规范标点）
    3. 数据质量检查（全角/半角、空格等）
    4. 输出清洗报告

    使用方法:
        cleaner = DataCleaner()
        report = cleaner.analyze(chapters, sections)
        cleaner.clean_sections(sections)
        cleaner.save_report(report, "duplicate_detection_report.json")
    """

    # "通用"标签处理
    GENERIC_SUFFIXES = ["（通用）", "(通用)", "（综合）", "(综合)", "（综合与测试）", "(综合与测试)"]

    # Section 标签清洗模式（保留序号）
    SECTION_PREFIX_PATTERNS = [
        (r"^(\d+\.\d+)-(.+)$", "前缀如 3.1-"),           # 3.1-5的认识和加减法 → 序号=3.1, 标签=5的认识和加减法
        (r"^(\d+\.\d+\.\d+)-(.+)$", "前缀如 18.1.1-"),    # 18.1.1-xxx → 序号=18.1.1, 标签=xxx
        (r"^(\d+)-(.+)$", "纯数字前缀如 8-"),              # 8-xxx → 序号=8, 标签=xxx
    ]

    # Section 标签清洗模式（仅清洗）
    SECTION_CLEANUP_PATTERNS = [
        (r":$|：$", "末尾冒号"),
        (r"\s+$", "末尾空格"),
        (r"^\s+", "开头空格"),
        (r"\s{2,}", "多余空格"),
    ]

    # 全角/半角转换映射
    FULL_TO_HALF_WIDTH = {
        "０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
        "５": "5", "６": "6", "７": "7", "８": "8", "９": "9",
        "　": " ",  # 全角空格
    }

    def __init__(self):
        self.generic_duplicates: List[Dict] = []
        self.section_cleanups: List[Dict] = []
        self.quality_issues: List[Dict] = []

    def extract_section_order(self, label: str) -> Tuple[str, Optional[str], List[str]]:
        """
        提取 Section 序号并清洗标签

        根据 fanan.md 建议 #5：将序号单独存入 order_in_book 字段

        Args:
            label: 原始标签

        Returns:
            (清洗后的标签, 提取的序号, 清洗操作列表)
        """
        cleaned = label
        order_in_book = None
        operations = []

        # 1. 提取序号前缀
        for pattern, description in self.SECTION_PREFIX_PATTERNS:
            match = re.match(pattern, cleaned)
            if match:
                order_in_book = match.group(1)
                cleaned = match.group(2)
                operations.append(f"提取序号 {description}: '{order_in_book}'")
                break

        # 2. 清洗其他不规范内容
        for pattern, desc in self.SECTION_CLEANUP_PATTERNS:
            match = re.search(pattern, cleaned)
            if match:
                cleaned = re.sub(pattern, "", cleaned)
                operations.append(f"移除 {desc}: '{match.group()}'")

        # 3. 全角转半角
        for full, half in self.FULL_TO_HALF_WIDTH.items():
            if full in cleaned:
                cleaned = cleaned.replace(full, half)
                operations.append(f"全角转半角: '{full}' → '{half}'")

        cleaned = cleaned.strip()

        return cleaned, order_in_book, operations

    def clean_section_label(self, label: str) -> Tuple[str, List[str]]:
        """
        清洗 Section 标签（简化版，不保留序号）

        Args:
            label: 原始标签

        Returns:
            (清洗后的标签, 清洗操作列表)
        """
        cleaned, _, operations = self.extract_section_order(label)
        return cleaned, operations

    def detect_generic_duplicates(self, chapters: List[Dict]) -> List[Dict]:
        """
        检测"通用"标签的重复数据（检查包含关系）

        根据 fanan.md 建议 #1：检查与同名无"通用"字段的关系

        Args:
            chapters: 章节列表

        Returns:
            重复检测结果列表
        """
        duplicates = []
        non_generic_map: Dict[str, Dict] = {}
        generic_map: Dict[str, Dict] = {}

        # 分类：通用和非通用
        for chapter in chapters:
            label = chapter.get('label', '')
            has_generic = any(suffix in label for suffix in self.GENERIC_SUFFIXES)

            if has_generic:
                generic_map[chapter['id']] = chapter
            else:
                non_generic_map[label] = chapter

        # 检查带有"通用"标签的章节
        for chapter_id, chapter in generic_map.items():
            label = chapter.get('label', '')

            # 提取基础名称
            base_name = label
            for suffix in self.GENERIC_SUFFIXES:
                base_name = base_name.replace(suffix, "")
            base_name = base_name.strip()

            # 查找对应的非通用版本
            matching_non_generic = non_generic_map.get(base_name)

            # 检查关系类型
            relationship_type = "none"
            if matching_non_generic:
                # 检查是否在同一教材中
                generic_textbook = chapter.get('textbook_id', '')
                non_generic_textbook = matching_non_generic.get('textbook_id', '')

                if generic_textbook == non_generic_textbook:
                    relationship_type = "duplicate_same_textbook"
                else:
                    relationship_type = "duplicate_different_textbook"

            duplicate_info = {
                'generic_chapter': {
                    'id': chapter.get('id'),
                    'label': label,
                    'uri': chapter.get('uri'),
                    'textbook_id': chapter.get('textbook_id')
                },
                'base_name': base_name,
                'has_matching_non_generic': matching_non_generic is not None,
                'relationship_type': relationship_type,
                'non_generic_chapter': None
            }

            if matching_non_generic:
                duplicate_info['non_generic_chapter'] = {
                    'id': matching_non_generic.get('id'),
                    'label': matching_non_generic.get('label'),
                    'uri': matching_non_generic.get('uri'),
                    'textbook_id': matching_non_generic.get('textbook_id')
                }

            duplicates.append(duplicate_info)

        self.generic_duplicates = duplicates
        return duplicates

    def check_data_quality(self, sections: List[Dict]) -> List[Dict]:
        """
        数据质量检查

        检查全角/半角混用、多余空格等

        Args:
            sections: 小节列表

        Returns:
            质量问题列表
        """
        issues = []

        for section in sections:
            label = section.get('label', '')
            section_issues = []

            # 检查全角字符
            for full in self.FULL_TO_HALF_WIDTH.keys():
                if full in label:
                    section_issues.append({
                        'type': 'full_width_char',
                        'description': f'包含全角字符: {full}',
                        'severity': 'minor'
                    })

            # 检查多余空格
            if re.search(r"\s{2,}", label):
                section_issues.append({
                    'type': 'extra_space',
                    'description': '包含多余空格',
                    'severity': 'minor'
                })

            # 检查末尾空格
            if label.endswith(' ') or label.endswith('　'):
                section_issues.append({
                    'type': 'trailing_space',
                    'description': '末尾有空格',
                    'severity': 'minor'
                })

            if section_issues:
                issues.append({
                    'section_id': section.get('id'),
                    'label': label,
                    'issues': section_issues
                })

        self.quality_issues = issues
        return issues

    def analyze_sections(self, sections: List[Dict]) -> List[Dict]:
        """
        分析需要清洗的 Section

        Args:
            sections: 小节列表

        Returns:
            需要清洗的 Section 列表
        """
        cleanups = []

        for section in sections:
            label = section.get('label', '')
            cleaned_label, order_in_book, operations = self.extract_section_order(label)

            if operations:  # 有清洗操作
                cleanups.append({
                    'section_id': section.get('id'),
                    'original_label': label,
                    'cleaned_label': cleaned_label,
                    'order_in_book': order_in_book,  # 新增：保留序号
                    'operations': operations,
                    'uri': section.get('uri')
                })

        self.section_cleanups = cleanups
        return cleanups

    def analyze(self, chapters: List[Dict], sections: List[Dict]) -> Dict:
        """
        全面分析数据清洗需求

        Args:
            chapters: 章节列表
            sections: 小节列表

        Returns:
            分析报告
        """
        generic_duplicates = self.detect_generic_duplicates(chapters)
        section_cleanups = self.analyze_sections(sections)
        quality_issues = self.check_data_quality(sections)

        # 统计关系类型
        relationship_stats = Counter(d['relationship_type'] for d in generic_duplicates)

        report = {
            'summary': {
                'total_chapters': len(chapters),
                'total_sections': len(sections),
                'generic_duplicates_count': len(generic_duplicates),
                'section_cleanups_count': len(section_cleanups),
                'quality_issues_count': len(quality_issues),
                'relationship_stats': dict(relationship_stats),
            },
            'generic_duplicates': generic_duplicates,
            'section_cleanups': section_cleanups,
            'quality_issues': quality_issues,
            'recommendations': self._generate_recommendations(
                generic_duplicates, section_cleanups, quality_issues, relationship_stats
            )
        }

        return report

    def _generate_recommendations(
        self,
        generic_duplicates: List[Dict],
        section_cleanups: List[Dict],
        quality_issues: List[Dict],
        relationship_stats: Counter
    ) -> List[str]:
        """
        生成处理建议

        Args:
            generic_duplicates: 通用标签重复检测结果
            section_cleanups: Section 清洗列表
            quality_issues: 质量问题列表
            relationship_stats: 关系类型统计

        Returns:
            建议列表
        """
        recommendations = []

        # 通用标签建议（根据关系类型）
        if generic_duplicates:
            dup_same = relationship_stats.get('duplicate_same_textbook', 0)
            dup_diff = relationship_stats.get('duplicate_different_textbook', 0)
            no_match = relationship_stats.get('none', 0)

            if dup_same > 0:
                recommendations.append(
                    f"发现 {dup_same} 个'通用'标签章节与同教材同名章节重复，建议删除通用版本"
                )
            if dup_diff > 0:
                recommendations.append(
                    f"发现 {dup_diff} 个'通用'标签章节与其他教材同名章节重复，建议检查后处理"
                )
            if no_match > 0:
                recommendations.append(
                    f"发现 {no_match} 个'通用'标签章节无对应版本，建议检查是否为独立内容"
                )

        # Section 清洗建议
        if section_cleanups:
            has_order = sum(1 for s in section_cleanups if s['order_in_book'])
            recommendations.append(
                f"发现 {len(section_cleanups)} 个 Section 标签需要清洗（其中 {has_order} 个包含序号）"
            )
            if has_order > 0:
                recommendations.append(
                    f"建议将序号保留到 order_in_book 字段，清洗后标签为纯文本"
                )

        # 质量问题建议
        if quality_issues:
            recommendations.append(
                f"发现 {len(quality_issues)} 个 Section 存在质量问题（全角字符、多余空格等）"
            )

        if not recommendations:
            recommendations.append("数据质量良好，无需清洗")

        return recommendations

    def clean_sections(
        self,
        sections: List[Dict],
        save: bool = True,
        preserve_order: bool = True
    ) -> List[Dict]:
        """
        执行 Section 清洗

        Args:
            sections: 小节列表
            save: 是否更新原列表
            preserve_order: 是否保留序号到 order_in_book 字段

        Returns:
            清洗后的 Section 列表（或原列表如果 save=True）
        """
        cleaned_sections = []

        for section in sections:
            label = section.get('label', '')
            cleaned_label, order_in_book, operations = self.extract_section_order(label)

            if operations:
                # 创建清洗后的副本
                cleaned_section = section.copy()
                cleaned_section['label'] = cleaned_label
                cleaned_section['original_label'] = label

                # 保留序号（根据 fanan.md 建议）
                if preserve_order and order_in_book:
                    cleaned_section['order_in_book'] = order_in_book

                cleaned_section['cleaned'] = True
                cleaned_sections.append(cleaned_section)

                if save:
                    # 直接更新原对象
                    section['label'] = cleaned_label
                    section['original_label'] = label
                    if preserve_order and order_in_book:
                        section['order_in_book'] = order_in_book

        logger.info(f"清洗了 {len(cleaned_sections)} 个 Section 标签")
        return cleaned_sections if not save else sections

    def clean_chapters(
        self,
        chapters: List[Dict],
        delete_generic: bool = True
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        执行章节清洗（删除通用标签）

        Args:
            chapters: 章节列表
            delete_generic: 是否删除通用标签章节

        Returns:
            (清洗后的章节列表, 删除的章节列表)
        """
        if not delete_generic:
            return chapters, []

        cleaned_chapters = []
        deleted_chapters = []

        for chapter in chapters:
            label = chapter.get('label', '')
            has_generic = any(suffix in label for suffix in self.GENERIC_SUFFIXES)

            if has_generic:
                deleted_chapters.append(chapter)
            else:
                cleaned_chapters.append(chapter)

        logger.info(f"删除 {len(deleted_chapters)} 个'通用'标签章节")
        return cleaned_chapters, deleted_chapters

    def save_report(self, report: Dict, filepath: str):
        """
        保存分析报告

        Args:
            report: 分析报告
            filepath: 文件路径
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"保存清洗报告: {filepath}")

    def save_cleaned_data(
        self,
        data: List[Dict],
        filepath: str
    ):
        """
        保存清洗后的数据

        Args:
            data: 清洗后的数据列表
            filepath: 文件路径
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"保存清洗后的数据: {filepath}")

    def save_clean_log(
        self,
        deleted_chapters: List[Dict],
        cleaned_sections: List[Dict],
        filepath: str
    ):
        """
        保存清洗日志

        Args:
            deleted_chapters: 删除的章节列表
            cleaned_sections: 清洗的 Section 列表
            filepath: 文件路径
        """
        log = {
            'deleted_chapters': len(deleted_chapters),
            'deleted_chapter_details': [
                {'id': c['id'], 'label': c['label']}
                for c in deleted_chapters
            ],
            'cleaned_sections': len(cleaned_sections),
            'section_changes': [
                {
                    'id': s['id'],
                    'original': s.get('original_label', ''),
                    'cleaned': s['label'],
                    'order_in_book': s.get('order_in_book')
                }
                for s in cleaned_sections if s.get('cleaned')
            ],
            'timestamp': str(Path(filepath).stat().st_mtime if Path(filepath).exists() else '')
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

        logger.info(f"保存清洗日志: {filepath}")