#!/usr/bin/env python3
"""
合并推断知识点脚本

功能:
1. 加载推断的知识点 (textbook_kps_inferred.json)
2. 合并到主知识点文件 (textbook_kps.json)
3. 重新生成 IN_UNIT 关系
4. 输出合并报告

使用方法:
    python merge_inferred_kps.py
    python merge_inferred_kps.py --dry-run  # 仅预览，不保存
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict
from collections import Counter

# 添加项目根目录到 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from edukg.core.textbook.config import OUTPUT_DIR, OUTPUT_FILES, URI_PREFIX, GRADE_ENCODING
from edukg.core.textbook.uri_generator import URIGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InferredKPMerger:
    """推断知识点合并器"""

    def __init__(self):
        self.uri_generator = URIGenerator()
        self.kp_counter = 0

    def load_data(self) -> tuple:
        """加载数据文件"""
        # 加载原知识点
        kps_path = Path(OUTPUT_DIR) / OUTPUT_FILES["textbook_kps"]
        with open(kps_path, 'r', encoding='utf-8') as f:
            original_kps = json.load(f)

        # 加载推断知识点
        inferred_path = Path(OUTPUT_DIR) / "textbook_kps_inferred.json"
        if not inferred_path.exists():
            raise FileNotFoundError(f"推断知识点文件不存在: {inferred_path}")

        with open(inferred_path, 'r', encoding='utf-8') as f:
            inferred_results = json.load(f)

        # 加载章节（用于获取 section_id 映射）
        sections_path = Path(OUTPUT_DIR) / OUTPUT_FILES["sections"]
        with open(sections_path, 'r', encoding='utf-8') as f:
            sections = json.load(f)

        logger.info(f"加载原知识点: {len(original_kps)}")
        logger.info(f"加载推断结果: {len(inferred_results)}")
        logger.info(f"加载章节: {len(sections)}")

        return original_kps, inferred_results, sections

    def generate_kp_uri(self, stage: str, seq: int) -> str:
        """
        生成知识点 URI

        Args:
            stage: 学段
            seq: 序号

        Returns:
            URI 字符串
        """
        stage_code = 'primary' if stage == '小学' else ('middle' if stage == '初中' else 'high')
        return f"{URI_PREFIX}/instance/math#textbook-{stage_code}-{seq:05d}"

    def merge_kps(
        self,
        original_kps: List[Dict],
        inferred_results: List[Dict],
        sections: List[Dict]
    ) -> tuple:
        """
        合并知识点

        Args:
            original_kps: 原知识点列表
            inferred_results: 推断结果列表
            sections: 章节列表

        Returns:
            (合并后的知识点列表, 新增知识点列表, 更新的关系列表)
        """
        # 建立章节 ID 映射
        section_map = {s['id']: s for s in sections}

        # 建立现有知识点映射（按 section_id 分组）
        existing_by_section: Dict[str, List[Dict]] = {}
        for kp in original_kps:
            section_id = kp.get('section_id', '')
            if section_id not in existing_by_section:
                existing_by_section[section_id] = []
            existing_by_section[section_id].append(kp)

        # 统计
        new_kps = []
        updated_in_unit_relations = []

        # 确定起始序号
        max_seq = 0
        for kp in original_kps:
            uri = kp.get('uri', '')
            if 'textbook-' in uri:
                try:
                    seq_str = uri.split('-')[-1]
                    seq = int(seq_str)
                    max_seq = max(max_seq, seq)
                except ValueError:
                    pass

        self.kp_counter = max_seq + 1

        # 处理推断结果
        for result in inferred_results:
            section_id = result.get('section_id', '')
            section = section_map.get(section_id, {})

            if not section:
                logger.warning(f"找不到章节: {section_id}")
                continue

            # 获取推断的知识点
            inferred_kps = result.get('knowledge_points', [])
            confidence = result.get('confidence', 0)

            # 获取已有知识点名称（用于去重）
            existing_names = set()
            for kp in existing_by_section.get(section_id, []):
                existing_names.add(kp.get('label', ''))

            # 添加新知识点
            for kp_name in inferred_kps:
                if kp_name in existing_names:
                    continue  # 跳过重复

                # 生成 URI
                uri = self.generate_kp_uri(result.get('stage', '小学'), self.kp_counter)
                self.kp_counter += 1

                # 创建知识点节点
                new_kp = {
                    'uri': uri,
                    'label': kp_name,
                    'stage': result.get('stage', ''),
                    'grade': result.get('grade', ''),
                    'section_id': section_id,
                    'confidence': confidence,
                    'source': 'llm_inferred'
                }
                new_kps.append(new_kp)

                # 创建 IN_UNIT 关系
                relation = {
                    'kp_uri': uri,
                    'kp_name': kp_name,
                    'section_id': section_id,
                    'confidence': confidence
                }
                updated_in_unit_relations.append(relation)

                existing_names.add(kp_name)

        # 合并知识点列表
        merged_kps = original_kps + new_kps

        # 重新生成所有 IN_UNIT 关系
        all_in_unit_relations = []

        # 原有关系
        original_relations_path = Path(OUTPUT_DIR) / OUTPUT_FILES["in_unit_relations"]
        if original_relations_path.exists():
            with open(original_relations_path, 'r', encoding='utf-8') as f:
                original_relations = json.load(f)
            all_in_unit_relations.extend(original_relations)

        # 新增关系
        all_in_unit_relations.extend(updated_in_unit_relations)

        return merged_kps, new_kps, all_in_unit_relations

    def save_results(
        self,
        merged_kps: List[Dict],
        new_kps: List[Dict],
        all_relations: List[Dict],
        dry_run: bool = False
    ):
        """保存结果"""
        if dry_run:
            logger.info("\n=== 预览模式（不保存） ===")
            return

        # 保存合并后的知识点
        kps_path = Path(OUTPUT_DIR) / OUTPUT_FILES["textbook_kps"]
        with open(kps_path, 'w', encoding='utf-8') as f:
            json.dump(merged_kps, f, ensure_ascii=False, indent=2)
        logger.info(f"更新知识点文件: {kps_path}")

        # 保存关系
        relations_path = Path(OUTPUT_DIR) / OUTPUT_FILES["in_unit_relations"]
        with open(relations_path, 'w', encoding='utf-8') as f:
            json.dump(all_relations, f, ensure_ascii=False, indent=2)
        logger.info(f"更新关系文件: {relations_path}")

        # 保存合并报告
        report = {
            'original_kp_count': len(merged_kps) - len(new_kps),
            'new_kp_count': len(new_kps),
            'total_kp_count': len(merged_kps),
            'total_relations': len(all_relations)
        }

        report_path = Path(OUTPUT_DIR) / "merge_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"保存合并报告: {report_path}")


def main():
    parser = argparse.ArgumentParser(description='合并推断知识点')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不保存')

    args = parser.parse_args()

    merger = InferredKPMerger()

    try:
        # 加载数据
        original_kps, inferred_results, sections = merger.load_data()

        # 合并
        merged_kps, new_kps, all_relations = merger.merge_kps(
            original_kps, inferred_results, sections
        )

        # 统计
        logger.info("\n=== 合并结果 ===")
        logger.info(f"原知识点数: {len(original_kps)}")
        logger.info(f"新增知识点数: {len(new_kps)}")
        logger.info(f"合并后总数: {len(merged_kps)}")
        logger.info(f"IN_UNIT 关系数: {len(all_relations)}")

        # 按学段统计新增知识点
        by_stage = Counter(kp.get('stage', '未知') for kp in new_kps)
        logger.info("\n新增知识点分布:")
        for stage, count in by_stage.items():
            logger.info(f"  {stage}: {count}")

        # 按置信度统计
        if new_kps:
            high_conf = sum(1 for kp in new_kps if kp.get('confidence', 0) >= 0.8)
            mid_conf = sum(1 for kp in new_kps if 0.6 <= kp.get('confidence', 0) < 0.8)
            low_conf = sum(1 for kp in new_kps if kp.get('confidence', 0) < 0.6)
            logger.info("\n置信度分布:")
            logger.info(f"  高 (≥0.8): {high_conf}")
            logger.info(f"  中 (0.6-0.8): {mid_conf}")
            logger.info(f"  低 (<0.6): {low_conf}")

        # 保存
        merger.save_results(merged_kps, new_kps, all_relations, args.dry_run)

        if not args.dry_run:
            logger.info("\n✅ 合并完成!")

    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        logger.info("请先运行 'python infer_textbook_kp.py' 生成推断知识点")
        sys.exit(1)
    except Exception as e:
        logger.error(f"合并失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()