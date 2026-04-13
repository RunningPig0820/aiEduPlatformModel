#!/usr/bin/env python3
"""
为推断知识点补充教学属性

复用 KPAttributeInferer 为 LLM 推断的知识点补充：
- topic
- difficulty
- importance
- cognitive_level

使用方法:
    python enhance_inferred_kps.py
    python enhance_inferred_kps.py --stats
"""
import json
import logging
from pathlib import Path

# 添加项目路径
import sys
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from edukg.core.textbook.kp_attribute_inferer import KPAttributeInferer
from edukg.core.textbook.config import OUTPUT_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_data():
    """加载所需数据"""
    kps_file = OUTPUT_DIR / "textbook_kps.json"
    chapters_file = OUTPUT_DIR / "chapters.json"
    sections_file = OUTPUT_DIR / "sections.json"

    with open(kps_file, 'r', encoding='utf-8') as f:
        kps = json.load(f)

    with open(chapters_file, 'r', encoding='utf-8') as f:
        chapters = json.load(f)

    with open(sections_file, 'r', encoding='utf-8') as f:
        sections = json.load(f)

    # 构建章节 topic 映射
    chapter_topic_map = {ch.get('id'): ch.get('topic', '数与代数') for ch in chapters}

    # 构建 section -> chapter 映射
    section_chapter_map = {}
    for sec in sections:
        sec_id = sec.get('id')
        ch_id = sec.get('chapter_id')
        if sec_id and ch_id:
            section_chapter_map[sec_id] = ch_id

    logger.info(f"加载知识点: {len(kps)}, 章节: {len(chapters)}, 小节: {len(sections)}")

    return kps, chapter_topic_map, section_chapter_map


def enhance_inferred_kps(kps, chapter_topic_map, section_chapter_map):
    """为推断知识点补充属性"""
    inferer = KPAttributeInferer()

    # 识别推断知识点（缺少 difficulty 字段）
    inferred_count = 0
    enhanced_count = 0

    for kp in kps:
        # 只处理推断知识点（缺少属性）
        if kp.get('difficulty'):
            continue

        inferred_count += 1

        kp_name = kp.get('label', '')
        grade = kp.get('grade', '')
        section_id = kp.get('section_id', '')

        # 获取章节 topic
        chapter_id = section_chapter_map.get(section_id, '')
        chapter_topic = chapter_topic_map.get(chapter_id, '数与代数')

        # 推断属性
        try:
            attrs = inferer.infer_attributes(kp_name, grade, chapter_topic)

            # 更新知识点
            kp['difficulty'] = attrs['difficulty']
            kp['difficulty_source'] = attrs['difficulty_source']
            kp['importance'] = attrs['importance']
            kp['importance_source'] = attrs['importance_source']
            kp['cognitive_level'] = attrs['cognitive_level']
            kp['cognitive_level_source'] = attrs['cognitive_level_source']
            kp['topic'] = attrs['topic']
            kp['topic_source'] = attrs['topic_source']

            enhanced_count += 1

        except Exception as e:
            logger.warning(f"推断属性失败: {kp_name} - {e}")
            # 使用默认值
            kp['difficulty'] = 3
            kp['difficulty_source'] = '默认'
            kp['importance'] = '重要'
            kp['importance_source'] = '默认'
            kp['cognitive_level'] = '理解'
            kp['cognitive_level_source'] = '默认'
            kp['topic'] = chapter_topic
            kp['topic_source'] = 'chapter_topic:默认'
            enhanced_count += 1

    logger.info(f"处理推断知识点: {inferred_count}, 补充属性: {enhanced_count}")

    return kps


def save_enhanced_kps(kps):
    """保存增强后的知识点"""
    output_file = OUTPUT_DIR / "textbook_kps.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(kps, f, ensure_ascii=False, indent=2)

    logger.info(f"保存知识点: {output_file} ({len(kps)} 条)")


def show_stats():
    """显示统计"""
    kps_file = OUTPUT_DIR / "textbook_kps.json"

    with open(kps_file, 'r', encoding='utf-8') as f:
        kps = json.load(f)

    print("\n=== 知识点属性统计 ===")
    print(f"总知识点数: {len(kps)}")

    # 检查属性完整性
    missing_difficulty = sum(1 for kp in kps if not kp.get('difficulty'))
    missing_importance = sum(1 for kp in kps if not kp.get('importance'))
    missing_cognitive = sum(1 for kp in kps if not kp.get('cognitive_level'))
    missing_topic = sum(1 for kp in kps if not kp.get('topic'))

    print(f"\n属性完整性:")
    print(f"  difficulty 缺失: {missing_difficulty}")
    print(f"  importance 缺失: {missing_importance}")
    print(f"  cognitive_level 缺失: {missing_cognitive}")
    print(f"  topic 缺失: {missing_topic}")

    # Topic 分布
    topic_dist = {}
    for kp in kps:
        topic = kp.get('topic', '无')
        topic_dist[topic] = topic_dist.get(topic, 0) + 1

    print("\nTopic 分布:")
    for topic, count in sorted(topic_dist.items(), key=lambda x: -x[1]):
        print(f"  {topic}: {count}")

    # 难度分布
    diff_dist = {}
    for kp in kps:
        diff = kp.get('difficulty', 0)
        diff_dist[diff] = diff_dist.get(diff, 0) + 1

    print("\n难度分布:")
    for diff, count in sorted(diff_dist.items()):
        print(f"  难度{diff}: {count}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='为推断知识点补充属性')
    parser.add_argument('--stats', action='store_true', help='显示统计')
    parser.add_argument('--enhance', action='store_true', help='执行增强')

    args = parser.parse_args()

    if args.stats:
        show_stats()
        return

    # 执行增强
    logger.info("开始为推断知识点补充属性...")

    kps, chapter_topic_map, section_chapter_map = load_data()
    enhanced_kps = enhance_inferred_kps(kps, chapter_topic_map, section_chapter_map)
    save_enhanced_kps(enhanced_kps)

    # 显示统计
    show_stats()

    logger.info("\n✅ 完成!")


if __name__ == '__main__':
    main()