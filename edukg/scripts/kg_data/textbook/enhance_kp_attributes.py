#!/usr/bin/env python3
"""
知识点属性增强命令行入口

为 TextbookKP 增加教学属性（difficulty, importance, cognitive_level, topic）。

使用方法：
    # 分析属性分布
    python edukg/scripts/kg_data/enhance_kp_attributes.py --analyze

    # 执行增强（输出到 textbook_kps_enhanced.json）
    python edukg/scripts/kg_data/enhance_kp_attributes.py --enhance

    # 强制执行增强（输出到 textbook_kps_enhanced.json）
    python edukg/scripts/kg_data/enhance_kp_attributes.py --enhance --force

    # 合并到主文件
    python edukg/scripts/kg_data/enhance_kp_attributes.py --merge

    # 显示已有统计
    python edukg/scripts/kg_data/enhance_kp_attributes.py --stats
"""
import os
import argparse
import json
import logging
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KG_DATA_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_ROOT = os.path.abspath(os.path.join(KG_DATA_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 添加 ai-edu-ai-service 目录（用于加载 .env）
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

# 切换工作目录到 ai-edu-ai-service 以正确加载 .env 文件
os.chdir(AI_SERVICE_DIR)

from edukg.core.textbook.kp_attribute_inferer import KPAttributeInferer
from edukg.core.textbook.config import OUTPUT_DIR

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_data():
    """加载所需数据文件"""
    kps_file = OUTPUT_DIR / "textbook_kps.json"
    chapters_file = OUTPUT_DIR / "chapters.json"
    sections_file = OUTPUT_DIR / "sections.json"

    if not kps_file.exists():
        logger.error(f"知识点文件不存在: {kps_file}")
        return None, None, None

    with open(kps_file, "r", encoding="utf-8") as f:
        kps = json.load(f)

    with open(chapters_file, "r", encoding="utf-8") as f:
        chapters = json.load(f)

    with open(sections_file, "r", encoding="utf-8") as f:
        sections = json.load(f)

    logger.info(f"加载知识点: {len(kps)}")
    logger.info(f"加载章节: {len(chapters)}")
    logger.info(f"加载小节: {len(sections)}")

    return kps, chapters, sections


def analyze_attributes(kps, chapters, sections):
    """分析属性分布（预览）"""
    inferer = KPAttributeInferer()
    enhanced = inferer.infer_batch(kps, chapters, sections)
    inferer.print_summary()

    # 输出样本供审核
    print("\n=== 知识点推断样本（前10条） ===")
    for kp in enhanced[:10]:
        print(f"\n{kp['label']} ({kp['grade']})")
        print(f"  难度: {kp['difficulty']} [{kp['difficulty_source']}]")
        print(f"  重要性: {kp['importance']} [{kp['importance_source']}]")
        print(f"  认知层次: {kp['cognitive_level']} [{kp['cognitive_level_source']}]")
        print(f"  专题: {kp['topic']} [{kp['topic_source']}]")

    return enhanced


def enhance_kps(kps, chapters, sections, force=False):
    """执行属性增强"""
    enhanced_file = OUTPUT_DIR / "textbook_kps_enhanced.json"
    stats_file = OUTPUT_DIR / "kp_attributes_distribution.json"

    if enhanced_file.exists() and not force:
        logger.warning(f"增强文件已存在: {enhanced_file}")
        logger.warning("使用 --force 强制重新生成")
        return False

    inferer = KPAttributeInferer()
    enhanced = inferer.infer_batch(kps, chapters, sections)

    # 保存增强后的数据
    inferer.save_enhanced_data(enhanced, str(enhanced_file))
    logger.info(f"保存增强后的知识点: {enhanced_file}")

    # 保存统计报告
    inferer.save_stats_report(str(stats_file))
    logger.info(f"保存属性分布报告: {stats_file}")

    inferer.print_summary()
    return True


def merge_to_main():
    """合并属性到主文件"""
    enhanced_file = OUTPUT_DIR / "textbook_kps_enhanced.json"
    main_file = OUTPUT_DIR / "textbook_kps.json"

    if not enhanced_file.exists():
        logger.error(f"增强文件不存在: {enhanced_file}")
        logger.error("请先执行 --enhance")
        return False

    with open(enhanced_file, "r", encoding="utf-8") as f:
        enhanced_kps = json.load(f)

    # 直接覆盖主文件（增强文件包含原有字段+新属性）
    with open(main_file, "w", encoding="utf-8") as f:
        json.dump(enhanced_kps, f, ensure_ascii=False, indent=2)

    logger.info(f"合并属性到主文件: {main_file}")
    logger.info(f"总知识点: {len(enhanced_kps)}")

    # 清理临时文件
    # enhanced_file.unlink()
    logger.info(f"增强文件保留: {enhanced_file}")

    return True


def show_stats():
    """显示已有统计"""
    stats_file = OUTPUT_DIR / "kp_attributes_distribution.json"

    if not stats_file.exists():
        logger.error(f"统计文件不存在: {stats_file}")
        logger.error("请先执行 --enhance")
        return

    with open(stats_file, "r", encoding="utf-8") as f:
        stats = json.load(f)

    print("\n=== 知识点属性分布统计 ===")
    print(f"总知识点数: {stats['total_kps']}")

    print("\n难度分布:")
    for d, count in sorted(stats["difficulty_distribution"].items()):
        pct = count / stats["total_kps"] * 100 if stats["total_kps"] > 0 else 0
        print(f"  难度{d}: {count} ({pct:.1f}%)")

    print("\n重要性分布:")
    for imp, count in stats["importance_distribution"].items():
        pct = count / stats["total_kps"] * 100 if stats["total_kps"] > 0 else 0
        print(f"  {imp}: {count} ({pct:.1f}%)")

    print("\n认知层次分布:")
    for level, count in stats["cognitive_level_distribution"].items():
        pct = count / stats["total_kps"] * 100 if stats["total_kps"] > 0 else 0
        print(f"  {level}: {count} ({pct:.1f}%)")

    print("\n专题分布:")
    for topic, count in stats["topic_distribution"].items():
        pct = count / stats["total_kps"] * 100 if stats["total_kps"] > 0 else 0
        print(f"  {topic}: {count} ({pct:.1f}%)")


def main():
    parser = argparse.ArgumentParser(description="知识点属性增强")
    parser.add_argument("--analyze", action="store_true", help="分析属性分布（预览）")
    parser.add_argument("--enhance", action="store_true", help="执行属性增强")
    parser.add_argument("--force", action="store_true", help="强制重新生成")
    parser.add_argument("--merge", action="store_true", help="合并属性到主文件")
    parser.add_argument("--stats", action="store_true", help="显示已有统计")

    args = parser.parse_args()

    if not any([args.analyze, args.enhance, args.merge, args.stats]):
        parser.print_help()
        return

    # 已在脚本开头切换到 ai-edu-ai-service 目录

    if args.stats:
        show_stats()
        return

    # 加载数据
    kps, chapters, sections = load_data()
    if kps is None:
        return

    if args.analyze:
        analyze_attributes(kps, chapters, sections)
    elif args.enhance:
        enhance_kps(kps, chapters, sections, args.force)
    elif args.merge:
        merge_to_main()


if __name__ == "__main__":
    main()