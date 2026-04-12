#!/usr/bin/env python3
"""
章节专题增强命令行入口

功能:
1. 为 Chapter 增加 topic 字段（数与代数、图形与几何、统计与概率、综合与实践）
2. 输出专题分布统计报告
3. 合并到主文件 chapters.json

使用方法:
    python enhance_chapters.py --analyze    # 仅分析，输出报告
    python enhance_chapters.py --enhance    # 执行增强（更新 chapters.json）
    python enhance_chapters.py --stats      # 显示专题分布
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from edukg.core.textbook.chapter_enhancer import ChapterEnhancer
from edukg.core.textbook.config import OUTPUT_DIR, OUTPUT_FILES

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChapterEnhanceRunner:
    """章节专题增强运行器"""

    def __init__(self):
        self.enhancer = ChapterEnhancer()
        self.output_dir = Path(OUTPUT_DIR)

    def load_chapters(self) -> List[Dict]:
        """加载章节文件"""
        chapters_path = self.output_dir / OUTPUT_FILES["chapters"]
        if not chapters_path.exists():
            raise FileNotFoundError(f"章节文件不存在: {chapters_path}")

        with open(chapters_path, 'r', encoding='utf-8') as f:
            chapters = json.load(f)

        logger.info(f"加载 {len(chapters)} 个章节")
        return chapters

    def run_analyze(self) -> Dict:
        """
        运行分析流程（不修改原文件）

        Returns:
            专题分布报告
        """
        chapters = self.load_chapters()

        logger.info("\n=== 开始分析 ===")

        # 执行增强（不保存）
        enhanced_chapters = self.enhancer.enhance_chapters(chapters)

        # 获取分布报告
        report = self.enhancer.get_topic_distribution()

        # 保存报告
        report_path = self.output_dir / "topic_distribution.json"
        self.enhancer.save_report(str(report_path))

        # 保存增强后的数据（临时）
        enhanced_path = self.output_dir / "chapters_enhanced.json"
        self.enhancer.save_enhanced_data(enhanced_chapters, str(enhanced_path))

        # 打印摘要
        self.enhancer.print_summary()

        logger.info(f"\n报告已保存: {report_path}")
        logger.info(f"增强数据已保存: {enhanced_path}")

        return report

    def run_enhance(self, force: bool = False) -> Dict:
        """
        运行增强流程（更新 chapters.json）

        Args:
            force: 是否强制执行（不检查报告）

        Returns:
            增强结果
        """
        # 检查报告是否存在
        report_path = self.output_dir / "topic_distribution.json"
        if not report_path.exists() and not force:
            logger.error("请先运行 --analyze 生成分析报告")
            logger.info("运行: python enhance_chapters.py --analyze")
            return {'status': 'error', 'message': '请先分析'}

        chapters = self.load_chapters()

        logger.info("\n=== 开始增强 ===")

        # 执行增强
        enhanced_chapters = self.enhancer.enhance_chapters(chapters)

        # 保存到主文件
        chapters_path = self.output_dir / OUTPUT_FILES["chapters"]
        self.enhancer.save_enhanced_data(enhanced_chapters, str(chapters_path))

        # 保存报告
        self.enhancer.save_report(str(report_path))

        # 打印摘要
        self.enhancer.print_summary()

        logger.info(f"\n=== 增强完成 ===")
        logger.info(f"已更新章节文件: {chapters_path}")
        logger.info(f"专题分布报告: {report_path}")

        return {
            'status': 'success',
            'enhanced_count': len(enhanced_chapters),
            'topic_distribution': self.enhancer.get_topic_distribution()
        }

    def show_stats(self):
        """显示专题分布统计"""
        report_path = self.output_dir / "topic_distribution.json"

        if not report_path.exists():
            logger.error("报告不存在，请先运行 --analyze")
            return

        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)

        logger.info("\n=== 专题分布统计 ===")
        logger.info(f"总章节数: {report['total_chapters']}")
        logger.info("\n专题分布:")
        for topic, count in report['topic_counts'].items():
            percentage = report['topic_percentages'].get(topic, 0)
            logger.info(f"  {topic}: {count} ({percentage}%)")

        if report['unmatched_count'] > 0:
            logger.info(f"\n未匹配章节 ({report['unmatched_count']}):")
            for chapter in report['unmatched_chapters'][:10]:
                logger.info(f"  - {chapter['label']}")


def main():
    parser = argparse.ArgumentParser(description='章节专题增强')
    parser.add_argument('--analyze', action='store_true', help='仅分析，输出报告')
    parser.add_argument('--enhance', action='store_true', help='执行增强（更新 chapters.json）')
    parser.add_argument('--force', action='store_true', help='强制执行增强，不检查报告')
    parser.add_argument('--stats', action='store_true', help='显示专题分布统计')

    args = parser.parse_args()

    runner = ChapterEnhanceRunner()

    try:
        if args.stats:
            runner.show_stats()
            return

        if args.analyze:
            runner.run_analyze()
            return

        if args.enhance or args.force:
            runner.run_enhance(force=args.force)
            return

        # 默认：分析
        logger.info("默认执行分析模式")
        runner.run_analyze()

    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        logger.info("请先运行 'python generate_textbook_data.py' 生成数据")
        sys.exit(1)
    except Exception as e:
        logger.error(f"增强失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()