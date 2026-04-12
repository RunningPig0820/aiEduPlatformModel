#!/usr/bin/env python3
"""
知识点匹配命令行入口

功能:
1. 加载教材知识点数据
2. 从 Neo4j 获取 EduKG Concept 列表
3. 使用双模型投票匹配知识点
4. 输出 MATCHES_KG 关系
5. 支持断点续传

使用方法:
    python match_textbook_kp.py
    python match_textbook_kp.py --resume    # 断点续传
    python match_textbook_kp.py --dry-run   # 仅估算成本
    python match_textbook_kp.py --stats     # 显示已有统计
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

from edukg.core.textbook import KPMatcher
from edukg.core.textbook.config import OUTPUT_DIR, OUTPUT_FILES
from edukg.core.textbook.kp_matcher import estimate_match_cost, PROGRESS_DIR
from edukg.core.neo4j.client import Neo4jClient
from edukg.config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KPMatchRunner:
    """知识点匹配运行器"""

    def __init__(self):
        self.neo4j_client = Neo4jClient()
        self.matcher = KPMatcher()

    def close(self):
        self.neo4j_client.close()

    def load_textbook_kps(self) -> List[Dict]:
        """加载教材知识点"""
        filepath = Path(OUTPUT_DIR) / OUTPUT_FILES["textbook_kps"]
        if not filepath.exists():
            raise FileNotFoundError(f"教材知识点文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            kps = json.load(f)

        logger.info(f"加载 {len(kps)} 个教材知识点")
        return kps

    def load_kg_concepts(self) -> List[Dict]:
        """从 Neo4j 加载图谱知识点"""
        with self.neo4j_client.session() as session:
            result = session.run("""
                MATCH (c:Concept)
                OPTIONAL MATCH (s:Statement)-[:RELATED_TO]->(c)
                WITH c, collect(s.content) AS descriptions
                RETURN c.uri AS uri, c.label AS label, descriptions[0] AS description
                ORDER BY c.label
            """)

            concepts = []
            for record in result:
                concepts.append({
                    'uri': record['uri'],
                    'label': record['label'],
                    'description': record['description'] or ''
                })

            logger.info(f"从 Neo4j 加载 {len(concepts)} 个图谱知识点")
            return concepts

    def show_progress(self):
        """显示当前进度"""
        state = self.matcher.task_state.get_state()
        progress = state.get('progress', {})

        logger.info("\n=== 当前进度 ===")
        logger.info(f"任务状态: {state.get('status', 'unknown')}")
        logger.info(f"总知识点数: {progress.get('total', 0)}")
        logger.info(f"已完成: {progress.get('completed', 0)}")
        logger.info(f"待处理: {progress.get('pending', 0)}")

        if progress.get('completed', 0) > 0:
            logger.info(f"完成率: {progress['completed'] / progress.get('total', 1) * 100:.1f}%")

    async def run_match(self, dry_run: bool = False, resume: bool = True) -> Dict:
        """
        运行匹配流程

        Args:
            dry_run: 是否仅估算成本
            resume: 是否断点续传

        Returns:
            运行结果
        """
        # 加载数据
        textbook_kps = self.load_textbook_kps()

        if dry_run:
            # 仅估算成本
            cost = estimate_match_cost(len(textbook_kps))
            logger.info("\n=== 成本估算 ===")
            logger.info(f"教材知识点数量: {cost['textbook_kp_count']}")
            logger.info(f"预估精确匹配: {cost['estimated_exact_match']}")
            logger.info(f"预估 LLM 匹配: {cost['estimated_llm_match']}")
            logger.info(f"LLM 调用次数: {cost['llm_calls']}")
            logger.info(f"预估成本: {cost['estimated_cost_rmb']} 元")
            logger.info(f"说明: {cost['note']}")
            return cost

        # 显示当前进度（如果启用断点续传）
        if resume:
            self.show_progress()

        # 加载图谱知识点
        kg_concepts = self.load_kg_concepts()

        # 执行匹配
        logger.info(f"\n=== 开始匹配 ===")
        if resume:
            logger.info("断点续传已启用")

        results = await self.matcher.match_all(textbook_kps, kg_concepts, resume=resume)

        # 保存结果
        output_path = Path(OUTPUT_DIR) / OUTPUT_FILES["matches_kg_relations"]
        self.matcher.save_results(results, str(output_path))

        # 统计（使用新的 matched 字段）
        stats = self.matcher.get_stats()
        matched_count = sum(1 for r in results if r.get('matched', False))
        unmatched_count = len(results) - matched_count

        logger.info("\n=== 匹配结果 ===")
        logger.info(f"总知识点: {len(results)}")
        logger.info(f"精确匹配: {stats['exact_match']}")
        logger.info(f"LLM 匹配: {stats['llm_match']} (缓存命中: {stats['cache_hits']})")
        logger.info(f"未匹配: {stats['unmatched']}")
        if stats['errors'] > 0:
            logger.info(f"LLM 调用错误: {stats['errors']}")
        logger.info(f"匹配率: {matched_count / len(results) * 100:.1f}%")
        logger.info(f"输出文件: {output_path}")

        return {
            'total': len(results),
            'matched': matched_count,
            'exact_match': stats['exact_match'],
            'llm_match': stats['llm_match'],
            'cache_hits': stats['cache_hits'],
            'unmatched': stats['unmatched'],
            'errors': stats['errors'],
            'output_file': str(output_path)
        }

    def show_stats(self):
        """显示已有统计"""
        output_path = Path(OUTPUT_DIR) / OUTPUT_FILES["matches_kg_relations"]
        if not output_path.exists():
            logger.warning(f"匹配结果文件不存在: {output_path}")
            return

        with open(output_path, 'r', encoding='utf-8') as f:
            results = json.load(f)

        # 使用新的统计方式
        matched = sum(1 for r in results if r.get('matched', False))
        exact = sum(1 for r in results if r['method'] == 'exact_match')
        llm = sum(1 for r in results if r['method'] == 'llm_vote')
        from_cache = sum(1 for r in results if r.get('from_cache'))
        unmatched = len(results) - matched

        logger.info("\n=== 匹配统计 ===")
        logger.info(f"文件: {output_path}")
        logger.info(f"总知识点: {len(results)}")
        logger.info(f"匹配成功: {matched}")
        logger.info(f"  - 精确匹配: {exact}")
        logger.info(f"  - LLM 匹配: {llm} (缓存命中: {from_cache})")
        logger.info(f"未匹配: {unmatched}")
        logger.info(f"匹配率: {matched / len(results) * 100:.1f}%")

        # 显示进度状态
        self.show_progress()


def main():
    parser = argparse.ArgumentParser(description='知识点匹配')
    parser.add_argument('--dry-run', action='store_true', help='仅估算成本，不实际调用 LLM')
    parser.add_argument('--stats', action='store_true', help='显示已有结果统计')
    parser.add_argument('--resume', action='store_true', default=True, help='启用断点续传（默认启用）')
    parser.add_argument('--no-resume', action='store_true', help='禁用断点续传，从头开始')

    args = parser.parse_args()

    # 断点续传逻辑
    resume = not args.no_resume

    runner = KPMatchRunner()

    try:
        # 显示统计
        if args.stats:
            runner.show_stats()
            return

        # 运行匹配
        result = asyncio.run(runner.run_match(args.dry_run, resume=resume))

        if not args.dry_run:
            logger.info("\n✅ 匹配完成!")

    except FileNotFoundError as e:
        logger.error(f"文件不存在: {e}")
        logger.info("请先运行 'python generate_textbook_data.py' 生成教材数据")
        sys.exit(1)
    except Exception as e:
        logger.error(f"匹配失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        runner.close()


if __name__ == '__main__':
    main()