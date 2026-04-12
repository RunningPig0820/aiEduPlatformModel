"""
知识点属性推断器

为 TextbookKP 增加教学属性（difficulty, importance, cognitive_level, topic），
基于规则匹配，无需 LLM。

使用方法：
    inferer = KPAttributeInferer()
    attrs = inferer.infer_attributes("有理数的加法", "七年级", "数与代数")
    # 返回: {"difficulty": 3, "importance": "重要", "cognitive_level": "应用", "topic": "数与代数"}
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)


# ============================================================
# 规则映射表
# ============================================================

# 年级 → 基础难度 (1-5)
GRADE_BASE_DIFFICULTY = {
    # 小学 (基础阶段)
    "一年级": 1,
    "二年级": 1,
    "三年级": 2,
    "四年级": 2,
    "五年级": 3,
    "六年级": 3,
    # 初中 (发展阶段)
    "七年级": 3,
    "八年级": 4,
    "九年级": 4,
    # 高中 (深化阶段)
    "必修第一册": 4,
    "必修第二册": 4,
    "必修第三册": 5,
}

# 难度调整关键词 (±1)
DIFFICULTY_ADJUST_KEYWORDS = {
    # 难度增加
    "+1": [
        "综合", "应用", "拓展", "探究", "复杂",
        "推导", "证明", "推理", "分析",
        "混合", "复合", "进阶",
    ],
    # 难度降低
    "-1": [
        "认识", "初步", "简单", "基础",
        "概念", "入门", "基本",
    ],
}

# 重要性关键词映射
IMPORTANCE_KEYWORDS = {
    "核心": [
        # 基础概念
        "概念", "定义", "定理", "公理", "原理",
        # 核心运算
        "法则", "公式", "性质", "规律",
        # 核心术语
        "加法", "减法", "乘法", "除法", "方程", "函数",
    ],
    "重要": [
        # 应用类
        "运算", "计算", "方法", "技巧", "应用",
        # 关系类
        "关系", "比较", "判定", "条件",
        # 过程类
        "步骤", "过程", "解法",
    ],
    "了解": [
        # 拓展类
        "拓展", "阅读", "活动", "兴趣", "课外",
        # 辅助类
        "补充", "延伸", "选学", "实践",
    ],
}

# 认知层次关键词映射 (布卢姆分类法)
COGNITIVE_LEVEL_KEYWORDS = {
    "识记": [
        # 认知类
        "认识", "概念", "定义", "术语", "名称",
        # 记忆类
        "读", "写", "记", "背诵", "复述",
        # 初步类
        "初步", "了解", "知道",
    ],
    "理解": [
        # 理解类
        "理解", "意义", "含义", "解释", "说明",
        # 关系类
        "关系", "联系", "比较", "区别", "联系",
        # 性质类
        "性质", "规律", "特征", "特点",
    ],
    "应用": [
        # 运算类
        "计算", "运算", "求解", "解", "求",
        # 应用类
        "应用", "运用", "操作", "实践",
        # 方法类
        "方法", "步骤", "技巧",
    ],
    "分析": [
        # 推理类
        "证明", "推导", "推理", "分析", "论证",
        # 判断类
        "判定", "判断", "验证", "检验",
        # 综合类
        "综合", "归纳", "总结",
    ],
}

# 默认属性值
DEFAULT_ATTRIBUTES = {
    "difficulty": 3,
    "importance": "重要",
    "cognitive_level": "理解",
}


class KPAttributeInferer:
    """
    知识点属性推断器

    功能:
    1. 基于规则匹配推断知识点属性
    2. 无需 LLM，纯规则推断
    3. 支持批量处理

    属性说明:
    - difficulty: 难度等级 (1-5)
    - importance: 重要性 (核心/重要/了解)
    - cognitive_level: 认知层次 (识记/理解/应用/分析)
    - topic: 所属专题 (继承章节)
    """

    def __init__(self):
        self.stats = {
            "difficulty": Counter(),
            "importance": Counter(),
            "cognitive_level": Counter(),
            "topic": Counter(),
        }

    def infer_difficulty(self, kp_name: str, grade: str) -> tuple:
        """
        推断难度等级

        Args:
            kp_name: 知识点名称
            grade: 年级

        Returns:
            (难度等级, 来源说明) 例如 (4, "grade:七年级(+3) + kw:应用(+1)")
        """
        # 年级基础难度
        base = GRADE_BASE_DIFFICULTY.get(grade, 3)
        grade_name = grade if grade in GRADE_BASE_DIFFICULTY else f"默认({base})"

        # 关键词调整（净调整值）
        adjust = 0
        matched_kw = []
        for kw in DIFFICULTY_ADJUST_KEYWORDS["+1"]:
            if kw in kp_name:
                adjust += 1
                matched_kw.append(f"{kw}(+1)")
        for kw in DIFFICULTY_ADJUST_KEYWORDS["-1"]:
            if kw in kp_name:
                adjust -= 1
                matched_kw.append(f"{kw}(-1)")

        # 计算最终难度
        difficulty = max(1, min(5, base + adjust))

        # 来源说明
        if matched_kw:
            source = f"grade:{grade_name}({base}) + kw:{', '.join(matched_kw)}"
        else:
            source = f"grade:{grade_name}({base})"

        return difficulty, source

    def infer_importance(self, kp_name: str) -> tuple:
        """
        推断重要性

        匹配优先级：核心 > 重要 > 了解

        Args:
            kp_name: 知识点名称

        Returns:
            (重要性, 来源说明) 例如 ("核心", "kw:概念")
        """
        # 按优先级顺序：核心 > 重要 > 了解
        for level in ["核心", "重要", "了解"]:
            keywords = IMPORTANCE_KEYWORDS.get(level, [])
            for keyword in keywords:
                if keyword in kp_name:
                    return level, f"kw:{keyword}"

        return DEFAULT_ATTRIBUTES["importance"], "默认"

    def infer_cognitive_level(self, kp_name: str) -> tuple:
        """
        推断认知层次

        匹配优先级：分析 > 应用 > 理解 > 识记
        （高认知层次优先，因为复杂知识点通常包含多个层次）

        Args:
            kp_name: 知识点名称

        Returns:
            (认知层次, 来源说明) 例如 ("应用", "kw:运算")
        """
        # 按优先级顺序：分析 > 应用 > 理解 > 识记
        for level in ["分析", "应用", "理解", "识记"]:
            keywords = COGNITIVE_LEVEL_KEYWORDS.get(level, [])
            for keyword in keywords:
                if keyword in kp_name:
                    return level, f"kw:{keyword}"

        return DEFAULT_ATTRIBUTES["cognitive_level"], "默认"

    def infer_attributes(
        self,
        kp_name: str,
        grade: str,
        section_topic: str,
    ) -> Dict:
        """
        推断所有属性

        Args:
            kp_name: 知识点名称
            grade: 年级
            section_topic: 所属章节的专题

        Returns:
            属性字典，包含属性值和来源说明
            {
                "difficulty": int,
                "difficulty_source": str,
                "importance": str,
                "importance_source": str,
                "cognitive_level": str,
                "cognitive_level_source": str,
                "topic": str,
                "topic_source": str,
            }
        """
        difficulty, difficulty_source = self.infer_difficulty(kp_name, grade)
        importance, importance_source = self.infer_importance(kp_name)
        cognitive_level, cognitive_level_source = self.infer_cognitive_level(kp_name)

        # topic 直接继承章节
        topic = section_topic if section_topic else "其他"
        topic_source = f"chapter_topic:{topic}"

        return {
            "difficulty": difficulty,
            "difficulty_source": difficulty_source,
            "importance": importance,
            "importance_source": importance_source,
            "cognitive_level": cognitive_level,
            "cognitive_level_source": cognitive_level_source,
            "topic": topic,
            "topic_source": topic_source,
        }

    def infer_batch(
        self,
        kps: List[Dict],
        chapters: List[Dict],
        sections: List[Dict],
    ) -> List[Dict]:
        """
        批量推断知识点属性

        Args:
            kps: 知识点列表
            chapters: 章节列表（含 topic）
            sections: 小节列表（含 chapter_id）

        Returns:
            增强后的知识点列表（含属性和来源说明）
        """
        # 构建 section → chapter 映射
        section_to_chapter = {}
        for section in sections:
            section_id = section.get("id", "")
            chapter_id = section.get("chapter_id", "")
            if chapter_id:
                section_to_chapter[section_id] = chapter_id

        # 构建 chapter → topic 映射
        chapter_to_topic = {}
        for chapter in chapters:
            chapter_id = chapter.get("id", "")
            topic = chapter.get("topic", "其他")
            chapter_to_topic[chapter_id] = topic

        enhanced = []
        for kp in kps:
            kp_name = kp.get("label", "")
            grade = kp.get("grade", "")
            section_id = kp.get("section_id", "")

            # 获取章节 topic
            chapter_id = section_to_chapter.get(section_id, "")
            topic = chapter_to_topic.get(chapter_id, "其他")

            # 推断属性（含来源）
            attrs = self.infer_attributes(kp_name, grade, topic)

            # 合并到知识点
            enhanced_kp = kp.copy()
            enhanced_kp["difficulty"] = attrs["difficulty"]
            enhanced_kp["difficulty_source"] = attrs["difficulty_source"]
            enhanced_kp["importance"] = attrs["importance"]
            enhanced_kp["importance_source"] = attrs["importance_source"]
            enhanced_kp["cognitive_level"] = attrs["cognitive_level"]
            enhanced_kp["cognitive_level_source"] = attrs["cognitive_level_source"]
            enhanced_kp["topic"] = attrs["topic"]
            enhanced_kp["topic_source"] = attrs["topic_source"]

            enhanced.append(enhanced_kp)

            # 统计
            self.stats["difficulty"][attrs["difficulty"]] += 1
            self.stats["importance"][attrs["importance"]] += 1
            self.stats["cognitive_level"][attrs["cognitive_level"]] += 1
            self.stats["topic"][attrs["topic"]] += 1

        logger.info(f"推断完成: {len(enhanced)} 个知识点")
        return enhanced

    def get_stats_report(self) -> Dict:
        """
        获取属性分布统计报告

        Returns:
            统计报告字典
        """
        total = sum(self.stats["difficulty"].values())

        return {
            "total_kps": total,
            "difficulty_distribution": dict(self.stats["difficulty"]),
            "importance_distribution": dict(self.stats["importance"]),
            "cognitive_level_distribution": dict(self.stats["cognitive_level"]),
            "topic_distribution": dict(self.stats["topic"]),
        }

    def print_summary(self):
        """打印属性分布摘要"""
        report = self.get_stats_report()

        print("\n=== 知识点属性分布统计 ===")
        print(f"总知识点数: {report['total_kps']}")

        print("\n难度分布:")
        for d, count in sorted(report["difficulty_distribution"].items()):
            pct = count / report["total_kps"] * 100 if report["total_kps"] > 0 else 0
            print(f"  难度{d}: {count} ({pct:.1f}%)")

        print("\n重要性分布:")
        for imp, count in report["importance_distribution"].items():
            pct = count / report["total_kps"] * 100 if report["total_kps"] > 0 else 0
            print(f"  {imp}: {count} ({pct:.1f}%)")

        print("\n认知层次分布:")
        for level, count in report["cognitive_level_distribution"].items():
            pct = count / report["total_kps"] * 100 if report["total_kps"] > 0 else 0
            print(f"  {level}: {count} ({pct:.1f}%)")

        print("\n专题分布:")
        for topic, count in report["topic_distribution"].items():
            pct = count / report["total_kps"] * 100 if report["total_kps"] > 0 else 0
            print(f"  {topic}: {count} ({pct:.1f}%)")

    def save_enhanced_data(self, kps: List[Dict], filepath: str):
        """
        保存增强后的数据

        Args:
            kps: 增强后的知识点列表
            filepath: 文件路径
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(kps, f, ensure_ascii=False, indent=2)

        logger.info(f"保存增强后的知识点: {filepath}")

    def save_stats_report(self, filepath: str):
        """
        保存属性分布统计报告

        Args:
            filepath: 文件路径
        """
        report = self.get_stats_report()

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"保存属性分布报告: {filepath}")