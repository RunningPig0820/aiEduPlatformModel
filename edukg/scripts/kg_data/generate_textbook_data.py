#!/usr/bin/env python3
"""
教材数据生成命令行入口

功能:
1. 从原始 JSON 文件生成标准格式 JSON
2. 输出教材、章节、小节、知识点节点
3. 输出 CONTAINS、IN_UNIT 关系

使用方法:
    python generate_textbook_data.py
    python generate_textbook_data.py --dry-run  # 仅显示统计
    python generate_textbook_data.py --stats    # 显示已有统计
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# 添加项目根目录到 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from edukg.core.textbook import TextbookDataGenerator
from edukg.core.textbook.config import OUTPUT_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='教材数据生成')
    parser.add_argument('--dry-run', action='store_true', help='仅显示统计，不生成文件')
    parser.add_argument('--stats', action='store_true', help='显示已有数据统计')
    parser.add_argument('--output-dir', type=str, help='输出目录路径')

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else OUTPUT_DIR

    generator = TextbookDataGenerator(output_dir=output_dir)

    # 显示已有统计
    if args.stats:
        summary_file = output_dir / "import_summary.json"
        if summary_file.exists():
            import json
            with open(summary_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            logger.info("\n=== 已有数据统计 ===")
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")
        else:
            logger.warning(f"统计文件不存在: {summary_file}")
        return

    # Dry-run 模式
    if args.dry_run:
        files = generator.discover_files()
        logger.info(f"\n=== DRY-RUN 模式 ===")
        logger.info(f"发现 {len(files)} 个教材 JSON 文件")
        for f in files[:5]:
            logger.info(f"  - {f.name}")
        if len(files) > 5:
            logger.info(f"  ... 还有 {len(files) - 5} 个文件")
        logger.info(f"\n输出目录: {output_dir}")
        logger.info(f"\n运行 'python generate_textbook_data.py' 生成数据")
        return

    # 生成数据
    logger.info("\n=== 开始生成教材数据 ===")
    results = generator.generate_all()

    logger.info("\n=== 输出文件 ===")
    for key, path in results.items():
        logger.info(f"  {key}: {path}")

    logger.info("\n✅ 数据生成完成!")


if __name__ == '__main__':
    main()