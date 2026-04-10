#!/usr/bin/env python3
"""
前置关系推断命令行入口

功能:
1. 从 Neo4j 加载知识点数据
2. 使用双模型投票推断前置关系
3. 输出 JSON 文件（手动验证后导入）

使用方法:
    python infer_prerequisites.py
    python infer_prerequisites.py --dry-run  # 仅估算成本
    python infer_prerequisites.py --batch-size 20
"""
import os
import sys
import json
import argparse
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any

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

from edukg.core.llm_inference import DualModelVoter, PrerequisiteInferer
from edukg.core.llm_inference.config import (
    BATCH_SIZE,
    OUTPUT_DIR,
    LLM_PREREQ_FILE,
)
from edukg.core.llm_inference.prerequisite_inferer import estimate_inference_cost
from edukg.core.neo4j.client import Neo4jClient
from edukg.config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PrerequisiteInferenceRunner:
    """前置关系推断运行器"""

    def __init__(self, batch_size: int = BATCH_SIZE):
        self.batch_size = batch_size
        self.neo4j_client = Neo4jClient()
        self.voter = DualModelVoter()
        self.inferer = PrerequisiteInferer(self.voter)

    def close(self):
        self.neo4j_client.close()

    def load_concepts_from_neo4j(self) -> List[Dict]:
        """
        从 Neo4j 加载知识点数据

        Returns:
            知识点列表
        """
        with self.neo4j_client.session() as session:
            # 查询 Concept 节点
            result = session.run("""
                MATCH (c:Concept)
                OPTIONAL MATCH (s:Statement)-[:RELATED_TO]->(c)
                WITH c, collect(s.content) AS descriptions
                RETURN c.uri AS uri, c.label AS name, descriptions[0] AS description
                ORDER BY c.label
            """)

            concepts = []
            for record in result:
                concepts.append({
                    'uri': record['uri'],
                    'name': record['name'],
                    'description': record['description'] or ''
                })

            logger.info(f"从 Neo4j 加载 {len(concepts)} 个知识点")
            return concepts

    def generate_kp_pairs(self, concepts: List[Dict]) -> List[Dict]:
        """
        生成待推断的知识点对

        Args:
            concepts: 知识点列表

        Returns:
            知识点对列表

        Note:
            这是一个简化版本，实际应该基于启发式规则筛选候选对，
            例如: 同一章节、同一类型、有 RELATED_TO 关系等。
        """
        # 简化版本: 每个知识点与前后 5 个知识点配对
        pairs = []
        n = len(concepts)

        for i, kp_a in enumerate(concepts):
            # 与前后 5 个知识点配对
            for j in range(max(0, i - 5), min(n, i + 6)):
                if i != j:
                    kp_b = concepts[j]
                    pairs.append({
                        'kp_a': kp_a,
                        'kp_b': kp_b
                    })

        logger.info(f"生成 {len(pairs)} 个知识点对")
        return pairs

    async def run_inference(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        运行推断流程

        Args:
            dry_run: 是否仅估算成本

        Returns:
            运行结果
        """
        # 加载知识点
        concepts = self.load_concepts_from_neo4j()

        if dry_run:
            # 仅估算成本
            cost = estimate_inference_cost(len(concepts))
            logger.info("\n=== 成本估算 ===")
            logger.info(f"知识点数量: {cost['kp_count']}")
            logger.info(f"预估知识点对: {cost['estimated_pairs']}")
            logger.info(f"LLM 调用次数: {cost['llm_calls']}")
            logger.info(f"  - GLM-4-flash: {cost['glm_calls']} (免费)")
            logger.info(f"  - DeepSeek: {cost['deepseek_calls']}")
            logger.info(f"预估成本: {cost['estimated_cost_rmb']} 元")
            logger.info(f"说明: {cost['note']}")
            return cost

        # 生成知识点对
        pairs = self.generate_kp_pairs(concepts)

        # 执行推断
        logger.info(f"\n=== 开始推断 ===")
        logger.info(f"知识点对数量: {len(pairs)}")
        logger.info(f"批处理大小: {self.batch_size}")

        results = await self.inferer.infer_batch(pairs)

        # 保存结果
        output_path = self.inferer.save_results(results, LLM_PREREQ_FILE)

        # 统计
        prereq_count = sum(1 for r in results if r['relation_type'] == 'PREREQUISITE')
        candidate_count = sum(1 for r in results if r['relation_type'] == 'PREREQUISITE_CANDIDATE')

        logger.info("\n=== 推断结果 ===")
        logger.info(f"PREREQUISITE: {prereq_count}")
        logger.info(f"PREREQUISITE_CANDIDATE: {candidate_count}")
        logger.info(f"输出文件: {output_path}")

        return {
            'total_pairs': len(pairs),
            'prerequisite': prereq_count,
            'candidate': candidate_count,
            'output_file': output_path
        }


def main():
    parser = argparse.ArgumentParser(description='前置关系推断')
    parser.add_argument('--dry-run', action='store_true', help='仅估算成本，不实际调用 LLM')
    parser.add_argument('--batch-size', type=int, default=BATCH_SIZE, help='批处理大小')
    parser.add_argument('--stats', action='store_true', help='显示已有结果统计')

    args = parser.parse_args()

    runner = PrerequisiteInferenceRunner(args.batch_size)

    try:
        # 显示统计
        if args.stats:
            output_file = Path(OUTPUT_DIR) / LLM_PREREQ_FILE
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)

                prereq = sum(1 for r in results if r['relation_type'] == 'PREREQUISITE')
                candidate = sum(1 for r in results if r['relation_type'] == 'PREREQUISITE_CANDIDATE')

                logger.info("\n=== 结果统计 ===")
                logger.info(f"文件: {output_file}")
                logger.info(f"PREREQUISITE: {prereq}")
                logger.info(f"PREREQUISITE_CANDIDATE: {candidate}")
            else:
                logger.warning(f"结果文件不存在: {output_file}")
            return

        # 运行推断
        result = asyncio.run(runner.run_inference(args.dry_run))

        if not args.dry_run:
            logger.info("\n✅ 推断完成!")

    except Exception as e:
        logger.error(f"推断失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        runner.close()


if __name__ == '__main__':
    main()