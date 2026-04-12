"""
章节专题增强器

为 Chapter 增加 topic 字段，标注所属专题（数与代数、图形与几何、统计与概率、综合与实践）。
根据 fanan.md 建议 #2：增加"单元/专题"层级，支持跨年级知识进阶。

使用方法：
    enhancer = ChapterEnhancer()
    topic = enhancer.assign_topic("有理数")  # → "数与代数"
    enhanced = enhancer.enhance_chapters(chapters)
    enhancer.save_report(enhanced, "topic_distribution.json")
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class ChapterEnhancer:
    """
    章节专题增强器

    功能:
    1. 基于章节名称匹配专题（规则匹配，无 LLM）
    2. 批量增强章节，添加 topic 字段
    3. 输出专题分布统计报告

    专题分类（人教版数学）：
    - 数与代数：有理数、整式、方程、函数等
    - 图形与几何：几何图形、三角形、圆等
    - 统计与概率：数据的收集、概率等
    - 综合与实践：数学活动、课题学习等
    """

    # 人教版数学专题分类映射
    MATH_TOPICS = {
        "数与代数": [
            # 数的认识
            "有理数", "有理数的加减", "有理数的乘除", "有理数的乘方",
            "实数", "平方根", "立方根", "二次根式",
            "正数和负数", "相反数", "绝对值", "负数",
            "分数", "小数", "百分数",
            "万以内数的认识", "大数的认识", "数的认识",
            "认识时间", "时间", "认识钟表", "时、分、秒", "年、月、日",
            # 运算
            "整式的加减", "整式的乘法", "整式的除法", "分式",
            "一元一次方程", "二元一次方程", "一元二次方程", "分式方程", "简易方程",
            "不等式", "一元一次不等式",
            "代数式", "多项式", "单项式",
            "万以内的加法和减法", "加减法", "加法和减法",
            "有余数的除法", "除数是一位数的除法", "除数是两位数的除法", "除法",
            "多位数乘一位数", "两位数乘两位数", "三位数乘两位数", "乘法",
            "四则运算", "运算定律", "混合运算",
            "倍的认识", "因数与倍数", "倍数",
            "乘法口诀", "表内乘法", "表内除法",
            # 函数与比例
            "函数", "一次函数", "二次函数", "反比例函数", "数列",
            "比例", "正比例", "反比例", "比",
            # 集合与逻辑
            "集合与常用逻辑用语", "集合",
            # 其他代数
            "认识人民币", "认识长度", "认识面积",
            "找规律", "数学思考",
            "计数原理",
        ],
        "图形与几何": [
            # 基础图形
            "几何图形", "几何图形初步", "立体图形", "平面图形",
            "点、线、面", "直线、射线、线段",
            "角", "角的度量", "角的比较",
            "相交线", "平行线", "相交线与平行线",
            # 三角形
            "三角形", "三角形的边", "三角形的角",
            "全等三角形", "相似三角形", "相似",
            "等腰三角形", "直角三角形", "勾股定理",
            # 四边形
            "四边形", "平行四边形", "矩形", "菱形", "正方形",
            "长方体和正方体",
            "多边形", "多边形的内角",
            # 圆
            "圆", "圆的性质", "圆周角",
            # 变换
            "图形的旋转", "图形的平移", "图形的对称", "旋转",
            "轴对称", "中心对称",
            "图形的运动",
            # 测量
            "图形的认识", "图形的测量", "测量",
            "长度单位", "面积单位", "体积单位",
            "克和千克", "公顷和平方千米",
            "周长", "面积", "体积",
            "长方形", "正方形", "圆形",
            # 位置与观察
            "位置与方向", "观察物体", "位置", "投影与视图",
            # 角度
            "直角", "锐角", "钝角",
            "认识图形", "拼组图形",
        ],
        "统计与概率": [
            "数据的收集", "数据的整理", "数据的描述", "数据的分析",
            "分类与整理", "数据收集整理",
            "统计", "统计图表", "统计图",
            "平均数", "中位数", "众数",
            "概率", "概率初步", "随机事件", "可能性", "随机变量及其分布",
            "频数", "频率",
            "抽样", "样本", "总体",
        ],
        "综合与实践": [
            "数学活动", "课题学习", "数学乐园", "数学广角", "搭配",
            "探究性学习", "实验与探究",
            "综合与测试", "本章小结",
            "复习", "整理和复习", "总复习",
            "准备课", "预备",
        ],
    }

    # 默认专题（未匹配时）
    DEFAULT_TOPIC = "其他"

    def __init__(self):
        self.topic_stats: Dict[str, int] = {}
        self.unmatched_chapters: List[Dict] = []

    def assign_topic(self, chapter_name: str) -> str:
        """
        为章节分配专题（基于规则匹配）

        Args:
            chapter_name: 章节名称

        Returns:
            专题名称（数与代数、图形与几何、统计与概率、综合与实践、其他）
        """
        # 清洗章节名称（移除序号、空格等）
        cleaned_name = chapter_name.strip()

        # 移除可能的序号前缀
        import re
        cleaned_name = re.sub(r'^[\d\.\-\s]+', '', cleaned_name)
        cleaned_name = re.sub(r'[\:\：]\s*$', '', cleaned_name)

        # 遍历专题关键词
        for topic, keywords in self.MATH_TOPICS.items():
            for keyword in keywords:
                # 检查是否包含关键词
                if keyword in cleaned_name:
                    return topic

        # 未匹配，返回默认
        return self.DEFAULT_TOPIC

    def enhance_chapter(self, chapter: Dict) -> Dict:
        """
        增强单个章节

        Args:
            chapter: 章节数据

        Returns:
            增强后的章节（含 topic 字段）
        """
        label = chapter.get('label', '')
        topic = self.assign_topic(label)

        enhanced = chapter.copy()
        enhanced['topic'] = topic

        # 记录未匹配的章节
        if topic == self.DEFAULT_TOPIC:
            self.unmatched_chapters.append({
                'id': chapter.get('id'),
                'label': label,
                'uri': chapter.get('uri')
            })

        return enhanced

    def enhance_chapters(self, chapters: List[Dict]) -> List[Dict]:
        """
        批量增强章节

        Args:
            chapters: 章节列表

        Returns:
            增强后的章节列表（含 topic 字段）
        """
        enhanced = []
        self.topic_stats = Counter()

        for chapter in chapters:
            enhanced_chapter = self.enhance_chapter(chapter)
            enhanced.append(enhanced_chapter)
            self.topic_stats[enhanced_chapter['topic']] += 1

        logger.info(f"增强 {len(enhanced)} 个章节")
        logger.info(f"专题分布: {dict(self.topic_stats)}")
        logger.info(f"未匹配章节: {len(self.unmatched_chapters)}")

        return enhanced

    def get_topic_distribution(self) -> Dict:
        """
        获取专题分布统计

        Returns:
            专题分布统计报告
        """
        total = sum(self.topic_stats.values())

        distribution = {
            'total_chapters': total,
            'topic_counts': dict(self.topic_stats),
            'topic_percentages': {
                topic: round(count / total * 100, 2) if total > 0 else 0
                for topic, count in self.topic_stats.items()
            },
            'unmatched_count': len(self.unmatched_chapters),
            'unmatched_chapters': self.unmatched_chapters,
        }

        return distribution

    def save_enhanced_data(self, chapters: List[Dict], filepath: str):
        """
        保存增强后的数据

        Args:
            chapters: 增强后的章节列表
            filepath: 文件路径
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chapters, f, ensure_ascii=False, indent=2)

        logger.info(f"保存增强后的章节: {filepath}")

    def save_report(self, filepath: str):
        """
        保存专题分布统计报告

        Args:
            filepath: 文件路径
        """
        report = self.get_topic_distribution()

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"保存专题分布报告: {filepath}")

    def print_summary(self):
        """打印专题分布摘要"""
        distribution = self.get_topic_distribution()

        print("\n=== 专题分布统计 ===")
        print(f"总章节数: {distribution['total_chapters']}")
        print("\n专题分布:")
        for topic, percentage in distribution['topic_percentages'].items():
            count = distribution['topic_counts'].get(topic, 0)
            print(f"  {topic}: {count} ({percentage}%)")

        if distribution['unmatched_count'] > 0:
            print(f"\n未匹配章节 ({distribution['unmatched_count']}):")
            for chapter in distribution['unmatched_chapters'][:10]:
                print(f"  - {chapter['label']}")
            if distribution['unmatched_count'] > 10:
                print(f"  ... 还有 {distribution['unmatched_count'] - 10} 个")