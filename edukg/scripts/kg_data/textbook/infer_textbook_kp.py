#!/usr/bin/env python3
"""
教学知识点推断命令行入口

功能:
1. 分析缺失知识点的章节（小学3-6年级、高中）
2. 使用 LLM 推断教学知识点
3. 输出推断结果
4. 支持断点续传

使用方法:
    python infer_textbook_kp.py                  # 推断所有缺失章节
    python infer_textbook_kp.py --resume         # 断点续传
    python infer_textbook_kp.py --stage primary  # 仅推断小学
    python infer_textbook_kp.py --dry-run        # 仅分析，不推断
    python infer_textbook_kp.py --stats          # 显示当前进度
"""
import os
import sys
import json
import argparse
import logging
import asyncio
from pathlib import Path
from typing import List, Dict

# 添加项目根目录到 sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 添加 ai-edu-ai-service 目录到 sys.path 以加载 config
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai-edu-ai-service")
if AI_SERVICE_DIR not in sys.path:
    sys.path.insert(0, AI_SERVICE_DIR)

# 切换工作目录到 ai-edu-ai-service 以正确加载 .env 文件
os.chdir(AI_SERVICE_DIR)

from edukg.core.llm_inference.textbook_kp_inferer import TextbookKPInferer
from edukg.core.textbook.config import OUTPUT_DIR, OUTPUT_FILES

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TextbookKPInferRunner:
    """教学知识点推断运行器"""

    def __init__(self):
        self.inferer = TextbookKPInferer()

    def load_sections(self) -> List[Dict]:
        """加载章节和知识点数据"""
        sections_path = Path(OUTPUT_DIR) / OUTPUT_FILES["sections"]
        textbook_kps_path = Path(OUTPUT_DIR) / OUTPUT_FILES["textbook_kps"]
        textbooks_path = Path(OUTPUT_DIR) / OUTPUT_FILES["textbooks"]

        if not sections_path.exists():
            raise FileNotFoundError(f"章节文件不存在: {sections_path}")

        if not textbook_kps_path.exists():
            raise FileNotFoundError(f"知识点文件不存在: {textbook_kps_path}")

        if not textbooks_path.exists():
            raise FileNotFoundError(f"教材文件不存在: {textbooks_path}")

        # 加载章节
        with open(sections_path, 'r', encoding='utf-8') as f:
            sections = json.load(f)

        # 加载知识点
        with open(textbook_kps_path, 'r', encoding='utf-8') as f:
            textbook_kps = json.load(f)

        # 加载教材（用于获取 stage/grade）
        with open(textbooks_path, 'r', encoding='utf-8') as f:
            textbooks = json.load(f)

        # 创建 textbook_id -> textbook 映射
        textbook_map = {tb.get('id'): tb for tb in textbooks}

        logger.info(f"加载 {len(sections)} 个章节，{len(textbook_kps)} 个知识点，{len(textbooks)} 个教材")

        return sections, textbook_kps, textbook_map

    def analyze_missing_kps(
        self,
        sections: List[Dict],
        textbook_kps: List[Dict],
        textbook_map: Dict[str, Dict],
        stage_filter: str = None
    ) -> List[Dict]:
        """
        分析缺失知识点的章节

        Args:
            sections: 章节列表
            textbook_kps: 知识点列表
            textbook_map: 教材 ID -> 教材数据映射
            stage_filter: 学段筛选（primary/middle/high）

        Returns:
            缺失知识点的章节列表
        """
        # 按小节 ID 分组知识点
        kp_by_section: Dict[str, List[str]] = {}
        for kp in textbook_kps:
            section_id = kp.get('section_id')
            if section_id:
                if section_id not in kp_by_section:
                    kp_by_section[section_id] = []
                kp_by_section[section_id].append(kp.get('label', ''))

        # 加载 chapters 获取 chapter_name
        chapters_path = Path(OUTPUT_DIR) / OUTPUT_FILES["chapters"]
        chapters = []
        if chapters_path.exists():
            with open(chapters_path, 'r', encoding='utf-8') as f:
                chapters = json.load(f)
        chapter_map = {ch.get('id'): ch for ch in chapters}

        # 筛选缺失知识点的章节
        missing_sections = []

        for section in sections:
            # 通过 textbook_id 获取 stage/grade
            textbook_id = section.get('textbook_id', '')
            textbook = textbook_map.get(textbook_id, {})
            stage = textbook.get('stage', '')
            grade = textbook.get('grade', '')
            semester = textbook.get('semester', '')

            # 学段筛选
            if stage_filter:
                stage_map = {'primary': '小学', 'middle': '初中', 'high': '高中'}
                if stage != stage_map.get(stage_filter, ''):
                    continue

            section_id = section.get('id', '')
            existing_kps = kp_by_section.get(section_id, [])

            # 通过 chapter_id 获取 chapter_name
            chapter_id = section.get('chapter_id', '')
            chapter = chapter_map.get(chapter_id, {})
            chapter_name = chapter.get('label', '')

            # 判断是否需要推断
            need_infer = False

            # 小学3-6年级数据缺失（原始 JSON 文件 knowledge_points 为空）
            # 说明：小学1-2年级有部分知识点，初中7-9年级知识点完整（约252个），无需推断
            if stage == '小学' and grade in ['三年级', '四年级', '五年级', '六年级']:
                need_infer = len(existing_kps) == 0

            # 高中数据缺失（原始 JSON 文件仅有综合测试标记）
            if stage == '高中':
                need_infer = len(existing_kps) == 0

            if need_infer:
                missing_sections.append({
                    'section_id': section_id,
                    'stage': stage,
                    'grade': grade,
                    'semester': semester,
                    'chapter_name': chapter_name,
                    'section_name': section.get('label', ''),
                    'existing_kps': existing_kps
                })

        return missing_sections

    async def run_infer(
        self,
        stage_filter: str = None,
        dry_run: bool = False,
        resume: bool = True
    ) -> Dict:
        """
        运行推断流程

        Args:
            stage_filter: 学段筛选
            dry_run: 是否仅分析
            resume: 是否断点续传

        Returns:
            运行结果
        """
        # 加载数据
        sections, textbook_kps, textbook_map = self.load_sections()

        # 分析缺失章节
        missing_sections = self.analyze_missing_kps(sections, textbook_kps, textbook_map, stage_filter)

        logger.info(f"\n=== 缺失知识点分析 ===")
        logger.info(f"总章节数: {len(sections)}")

        # 按学段统计
        by_stage = {}
        for s in missing_sections:
            stage = s.get('stage', '未知')
            by_stage[stage] = by_stage.get(stage, 0) + 1

        for stage, count in by_stage.items():
            logger.info(f"  {stage}: {count} 个章节缺失知识点")

        if dry_run:
            return {
                'total_sections': len(sections),
                'missing_sections': len(missing_sections),
                'by_stage': by_stage
            }

        if not missing_sections:
            logger.info("没有需要推断的章节")
            return {
                'total_sections': len(sections),
                'missing_sections': 0
            }

        # 显示当前进度
        if resume:
            self.inferer.show_progress()

        # 执行推断
        logger.info(f"\n=== 开始推断 ===")
        if resume:
            logger.info("断点续传已启用")

        results = await self.inferer.infer_batch(missing_sections, resume=resume)

        # 保存结果
        output_path = Path(OUTPUT_DIR) / "textbook_kps_inferred.json"
        self.inferer.save_results(results, str(output_path))

        # 统计
        from_cache = sum(1 for r in results if r.get('from_cache'))
        avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0
        total_kps = sum(len(r.get('knowledge_points', [])) for r in results)

        logger.info("\n=== 推断结果 ===")
        logger.info(f"推断章节: {len(results)}")
        logger.info(f"缓存命中: {from_cache}")
        logger.info(f"平均置信度: {avg_confidence:.2f}")
        logger.info(f"推断知识点总数: {total_kps}")
        logger.info(f"输出文件: {output_path}")

        return {
            'inferred_sections': len(results),
            'from_cache': from_cache,
            'avg_confidence': avg_confidence,
            'total_kps': total_kps,
            'output_file': str(output_path)
        }

    def show_stats(self):
        """显示进度统计"""
        self.inferer.show_progress()

        # 检查输出文件
        output_path = Path(OUTPUT_DIR) / "textbook_kps_inferred.json"
        if output_path.exists():
            with open(output_path, 'r', encoding='utf-8') as f:
                results = json.load(f)

            from_cache = sum(1 for r in results if r.get('from_cache'))
            avg_confidence = sum(r.get('confidence', 0) for r in results) / len(results) if results else 0

            logger.info(f"\n=== 推断结果文件 ===")
            logger.info(f"文件: {output_path}")
            logger.info(f"推断章节: {len(results)}")
            logger.info(f"缓存命中: {from_cache}")
            logger.info(f"平均置信度: {avg_confidence:.2f}")


def main():
    parser = argparse.ArgumentParser(description='教学知识点推断')
    parser.add_argument('--stage', choices=['primary', 'middle', 'high'], help='仅推断指定学段')
    parser.add_argument('--dry-run', action='store_true', help='仅分析缺失章节，不执行推断')
    parser.add_argument('--stats', action='store_true', help='显示当前进度')
    parser.add_argument('--resume', action='store_true', default=True, help='启用断点续传（默认启用）')
    parser.add_argument('--no-resume', action='store_true', help='禁用断点续传，从头开始')

    args = parser.parse_args()

    # 断点续传逻辑
    resume = not args.no_resume

    runner = TextbookKPInferRunner()

    try:
        # 显示统计
        if args.stats:
            runner.show_stats()
            return

        # 运行推断
        result = asyncio.run(runner.run_infer(
            stage_filter=args.stage,
            dry_run=args.dry_run,
            resume=resume
        ))

        if not args.dry_run:
            logger.info("\n✅ 推断完成!")
            logger.info("下一步: 运行 'python merge_inferred_kps.py' 合并知识点")

    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        logger.info("请先运行 'python generate_textbook_data.py' 生成教材数据")
        sys.exit(1)
    except Exception as e:
        logger.error(f"推断失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()