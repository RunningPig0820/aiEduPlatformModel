#!/usr/bin/env python3
"""
数据清洗命令行入口

功能:
1. 分析数据清洗需求（检测"通用"标签、不规范 Section 名称）
2. 输出重复检测报告
3. 执行数据清洗（需人工确认）

使用方法:
    python clean_textbook_data.py --analyze    # 仅分析，输出报告
    python clean_textbook_data.py --clean      # 执行清洗（需先确认报告）
    python clean_textbook_data.py --stats      # 显示清洗统计
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

from edukg.core.textbook.data_cleaner import DataCleaner
from edukg.core.textbook.config import OUTPUT_DIR, OUTPUT_FILES

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataCleanRunner:
    """数据清洗运行器"""

    def __init__(self):
        self.cleaner = DataCleaner()
        self.output_dir = Path(OUTPUT_DIR)

    def load_data(self) -> tuple:
        """加载数据文件"""
        # 加载章节
        chapters_path = self.output_dir / OUTPUT_FILES["chapters"]
        if not chapters_path.exists():
            raise FileNotFoundError(f"章节文件不存在: {chapters_path}")

        with open(chapters_path, 'r', encoding='utf-8') as f:
            chapters = json.load(f)

        # 加载小节
        sections_path = self.output_dir / OUTPUT_FILES["sections"]
        if not sections_path.exists():
            raise FileNotFoundError(f"小节文件不存在: {sections_path}")

        with open(sections_path, 'r', encoding='utf-8') as f:
            sections = json.load(f)

        logger.info(f"加载 {len(chapters)} 个章节, {len(sections)} 个小节")
        return chapters, sections

    def run_analyze(self) -> Dict:
        """
        运行分析流程

        Returns:
            分析报告
        """
        chapters, sections = self.load_data()

        logger.info("\n=== 开始分析 ===")

        # 执行分析
        report = self.cleaner.analyze(chapters, sections)

        # 保存报告
        report_path = self.output_dir / "duplicate_detection_report.json"
        self.cleaner.save_report(report, str(report_path))

        # 输出摘要
        summary = report['summary']
        logger.info("\n=== 分析结果 ===")
        logger.info(f"总章节数: {summary['total_chapters']}")
        logger.info(f"总小节数: {summary['total_sections']}")
        logger.info(f"'通用'标签重复: {summary['generic_duplicates_count']}")
        logger.info(f"Section 需清洗: {summary['section_cleanups_count']}")

        # 输出建议
        logger.info("\n=== 处理建议 ===")
        for i, rec in enumerate(report['recommendations'], 1):
            logger.info(f"{i}. {rec}")

        # 详细列出问题
        if report['generic_duplicates']:
            logger.info("\n=== '通用'标签详情 ===")
            for dup in report['generic_duplicates']:
                generic = dup['generic_chapter']
                logger.info(f"  - {generic['label']}")
                if dup['has_matching_non_generic']:
                    non_generic = dup['non_generic_chapter']
                    logger.info(f"    对应: {non_generic['label']}")

        if report['section_cleanups']:
            logger.info("\n=== Section 清洗详情 ===")
            for cleanup in report['section_cleanups']:
                logger.info(f"  - {cleanup['original_label']} → {cleanup['cleaned_label']}")
                for op in cleanup['operations']:
                    logger.info(f"    {op}")

        logger.info(f"\n报告已保存: {report_path}")

        return report

    def run_clean(self, force: bool = False) -> Dict:
        """
        运行清洗流程

        Args:
            force: 是否强制执行（不检查确认）

        Returns:
            清洗结果
        """
        # 检查报告是否存在
        report_path = self.output_dir / "duplicate_detection_report.json"
        if not report_path.exists() and not force:
            logger.error("请先运行 --analyze 生成分析报告")
            logger.info("运行: python clean_textbook_data.py --analyze")
            return {'status': 'error', 'message': '请先分析'}

        chapters, sections = self.load_data()

        logger.info("\n=== 开始清洗 ===")

        # 执行 Section 清洗
        cleaned_sections = self.cleaner.clean_sections(sections, save=True)

        # 保存清洗后的数据
        sections_path = self.output_dir / OUTPUT_FILES["sections"]
        self.cleaner.save_cleaned_data(sections, str(sections_path))

        # 保存清洗日志
        clean_log = {
            'cleaned_sections': len(cleaned_sections),
            'timestamp': str(Path(sections_path).stat().st_mtime),
            'changes': [
                {
                    'id': s.get('id'),
                    'original': s.get('original_label', ''),
                    'cleaned': s.get('label', '')
                }
                for s in sections if s.get('cleaned')
            ]
        }

        log_path = self.output_dir / "clean_log.json"
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(clean_log, f, ensure_ascii=False, indent=2)

        logger.info(f"\n=== 清洗完成 ===")
        logger.info(f"清洗 Section 数: {clean_log['cleaned_sections']}")
        logger.info(f"数据已更新: {sections_path}")
        logger.info(f"清洗日志: {log_path}")

        return clean_log

    def show_stats(self):
        """显示清洗统计"""
        # 检查报告
        report_path = self.output_dir / "duplicate_detection_report.json"
        if report_path.exists():
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)

            logger.info("\n=== 分析报告摘要 ===")
            summary = report['summary']
            logger.info(f"'通用'标签重复: {summary['generic_duplicates_count']}")
            logger.info(f"Section 需清洗: {summary['section_cleanups_count']}")

        # 检查清洗日志
        log_path = self.output_dir / "clean_log.json"
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                log = json.load(f)

            logger.info("\n=== 清洗日志 ===")
            logger.info(f"已清洗 Section: {log['cleaned_sections']}")

            if log['changes']:
                logger.info("变更详情:")
                for change in log['changes'][:5]:
                    logger.info(f"  - {change['original']} → {change['cleaned']}")
                if len(log['changes']) > 5:
                    logger.info(f"  ... 还有 {len(log['changes']) - 5} 个变更")


def main():
    parser = argparse.ArgumentParser(description='数据清洗')
    parser.add_argument('--analyze', action='store_true', help='仅分析，输出报告')
    parser.add_argument('--clean', action='store_true', help='执行清洗（需先确认报告）')
    parser.add_argument('--force', action='store_true', help='强制执行清洗，不检查报告')
    parser.add_argument('--stats', action='store_true', help='显示清洗统计')

    args = parser.parse_args()

    runner = DataCleanRunner()

    try:
        if args.stats:
            runner.show_stats()
            return

        if args.analyze:
            runner.run_analyze()
            return

        if args.clean or args.force:
            runner.run_clean(force=args.force)
            return

        # 默认：分析
        logger.info("默认执行分析模式")
        runner.run_analyze()

    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        logger.info("请先运行 'python generate_textbook_data.py' 生成数据")
        sys.exit(1)
    except Exception as e:
        logger.error(f"清洗失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()