"""
前置关系推断模块

使用双模型投票推断知识点之间的前置关系（PREREQUISITE）。
"""
import asyncio
import json
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

from edukg.core.llm_inference.dual_model_voter import DualModelVoter, vote_with_retry
from edukg.core.llm_inference.prompt_templates import format_prerequisite_prompt
from edukg.core.llm_inference.config import (
    BATCH_SIZE,
    RATE_LIMIT_DELAY,
    OUTPUT_DIR,
    LLM_PREREQ_FILE,
    TEACHES_BEFORE_FILE,
    DEFINITION_DEPS_FILE,
    FINAL_PREREQ_FILE,
)

logger = logging.getLogger(__name__)


class PrerequisiteInferer:
    """
    前置关系推断器

    使用双模型投票机制推断知识点之间的前置关系。

    使用方法:
        inferer = PrerequisiteInferer()
        results = await inferer.infer_batch(kp_pairs)
    """

    def __init__(self, voter: DualModelVoter = None):
        """
        初始化前置关系推断器

        Args:
            voter: DualModelVoter 实例（可选，默认创建新实例）
        """
        self.voter = voter or DualModelVoter()

    async def infer_batch(self, kp_pairs: List[Dict]) -> List[Dict]:
        """
        批量推断前置关系

        Args:
            kp_pairs: 知识点对列表，格式为：
                [{'kp_a': {'uri': ..., 'name': ..., 'description': ...},
                  'kp_b': {'uri': ..., 'name': ..., 'description': ...}}, ...]

        Returns:
            推断结果列表，格式为：
                [{'kp_a_uri': ..., 'kp_b_uri': ..., 'relation_type': 'PREREQUISITE',
                  'confidence': 0.9, 'source': 'llm_vote', 'reason': ...}, ...]
        """
        results = []
        total = len(kp_pairs)

        logger.info(f"开始批量推断 {total} 个知识点对")

        for i, pair in enumerate(kp_pairs):
            # 显示进度
            if (i + 1) % 10 == 0 or i == 0:
                logger.info(f"进度: {i + 1}/{total} ({(i + 1) / total * 100:.1f}%)")

            # 推断单个知识点对
            result = await self._infer_pair(pair)
            if result:
                results.append(result)

            # 速率限制
            if RATE_LIMIT_DELAY > 0:
                await asyncio.sleep(RATE_LIMIT_DELAY)

        # 统计
        prereq_count = sum(1 for r in results if r['relation_type'] == 'PREREQUISITE')
        candidate_count = sum(1 for r in results if r['relation_type'] == 'PREREQUISITE_CANDIDATE')

        logger.info(f"推断完成: PREREQUISITE={prereq_count}, PREREQUISITE_CANDIDATE={candidate_count}")

        return results

    async def _infer_pair(self, pair: Dict) -> Optional[Dict]:
        """
        推断单个知识点对的前置关系

        Args:
            pair: 知识点对

        Returns:
            推断结果或 None
        """
        kp_a = pair['kp_a']
        kp_b = pair['kp_b']

        # 格式化 Prompt
        prompt = format_prerequisite_prompt(
            kp_a_name=kp_a.get('name', ''),
            kp_a_description=kp_a.get('description', ''),
            kp_b_name=kp_b.get('name', ''),
            kp_b_description=kp_b.get('description', '')
        )

        # 带重试的投票
        vote_result = await vote_with_retry(self.voter, prompt)

        if not vote_result['consensus']:
            return None

        # 解析投票结果
        result = vote_result['result']
        decision = result.get('decision')
        confidence = result.get('confidence', 0.0)
        reason = result.get('primary_reason', '')

        # 如果不是前置关系，不记录
        if decision != True:
            return None

        # 确定关系类型
        relation_type = "PREREQUISITE" if confidence >= 0.8 else "PREREQUISITE_CANDIDATE"

        return {
            'kp_a_uri': kp_a.get('uri'),
            'kp_a_name': kp_a.get('name'),
            'kp_b_uri': kp_b.get('uri'),
            'kp_b_name': kp_b.get('name'),
            'relation_type': relation_type,
            'confidence': confidence,
            'source': 'llm_vote',
            'reason': reason
        }

    def infer_from_textbook_order(self, chapters: List[Dict]) -> List[Dict]:
        """
        基于教材顺序推断 TEACHES_BEFORE

        规则: 仅限章节内部，跨章节不推断

        Args:
            chapters: 章节列表，格式为：
                [{'id': ..., 'textbook_id': ..., 'sections': [{'id': ..., 'order': ..., 'kps': [...]}]}, ...]

        Returns:
            TEACHES_BEFORE 关系列表
        """
        results = []

        for chapter in chapters:
            sections = chapter.get('sections', [])

            # 章节内部的小节顺序
            for i, section_a in enumerate(sections):
                for j, section_b in enumerate(sections):
                    if i < j:
                        # section_a 在 section_b 前面
                        kps_a = section_a.get('kps', [])
                        kps_b = section_b.get('kps', [])

                        # 每个知识点对
                        for kp_a in kps_a:
                            for kp_b in kps_b:
                                results.append({
                                    'kp_a_uri': kp_a.get('uri'),
                                    'kp_b_uri': kp_b.get('uri'),
                                    'relation_type': 'TEACHES_BEFORE',
                                    'confidence': 1.0,
                                    'source': 'textbook_order',
                                    'chapter_id': chapter.get('id'),
                                    'section_a_order': section_a.get('order'),
                                    'section_b_order': section_b.get('order')
                                })

        logger.info(f"从教材顺序推断 {len(results)} 个 TEACHES_BEFORE 关系")
        return results

    def extract_from_definition(
        self,
        definition: str,
        kp_names: List[str],
        min_length: int = 3
    ) -> List[str]:
        """
        从定义文本中匹配知识点名称

        Args:
            definition: 知识点定义文本
            kp_names: 已知知识点名称列表
            min_length: 最小匹配长度（过滤太短的名称）

        Returns:
            匹配到的知识点名称列表
        """
        if not definition or not kp_names:
            return []

        matched = []
        definition_lower = definition.lower()

        for name in kp_names:
            # 过滤太短的名称
            if len(name) < min_length:
                continue

            # 检查是否出现在定义中
            if name.lower() in definition_lower:
                matched.append(name)

        return matched

    def save_results(self, results: List[Dict], filename: str) -> str:
        """
        保存推断结果到 JSON 文件

        Args:
            results: 推断结果列表
            filename: 文件名

        Returns:
            保存的文件路径
        """
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"保存结果到: {filepath}")
        return str(filepath)

    def load_results(self, filename: str) -> List[Dict]:
        """
        从 JSON 文件加载推断结果

        Args:
            filename: 文件名

        Returns:
            加载的结果列表
        """
        filepath = Path(OUTPUT_DIR) / filename

        if not filepath.exists():
            logger.warning(f"文件不存在: {filepath}")
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            results = json.load(f)

        logger.info(f"加载结果: {filepath}, 数量: {len(results)}")
        return results

    def fuse_results(
        self,
        teaches_before: List[Dict],
        definition_deps: List[Dict],
        llm_prereq: List[Dict]
    ) -> List[Dict]:
        """
        融合多种来源的前置关系

        Args:
            teaches_before: TEACHES_BEFORE 关系
            definition_deps: 定义依赖关系
            llm_prereq: LLM 推断的前置关系

        Returns:
            融合后的最终关系列表
        """
        # 使用字典去重（以 (kp_a_uri, kp_b_uri) 为 key）
        fused = {}

        # 1. TEACHES_BEFORE（仅作为教学顺序参考）
        for rel in teaches_before:
            key = (rel['kp_a_uri'], rel['kp_b_uri'])
            if key not in fused:
                fused[key] = rel

        # 2. 定义依赖（高可信度）
        for rel in definition_deps:
            key = (rel['kp_a_uri'], rel['kp_b_uri'])
            if key not in fused:
                # 定义依赖标记为 DEFINITION_DEP
                rel['relation_type'] = 'DEFINITION_DEP'
                fused[key] = rel
            else:
                # 如果已有 TEACHES_BEFORE，升级为 PREREQUISITE（多证据）
                existing = fused[key]
                if existing['relation_type'] == 'TEACHES_BEFORE':
                    fused[key] = {
                        'kp_a_uri': rel['kp_a_uri'],
                        'kp_b_uri': rel['kp_b_uri'],
                        'relation_type': 'PREREQUISITE',
                        'confidence': 0.9,
                        'source': 'multi_evidence',
                        'reason': '教材顺序 + 定义依赖'
                    }

        # 3. LLM 推断
        for rel in llm_prereq:
            key = (rel['kp_a_uri'], rel['kp_b_uri'])
            if key not in fused:
                fused[key] = rel
            else:
                existing = fused[key]
                # 如果已有其他证据，升级置信度
                if existing['relation_type'] in ['TEACHES_BEFORE', 'DEFINITION_DEP']:
                    fused[key] = {
                        'kp_a_uri': rel['kp_a_uri'],
                        'kp_b_uri': rel['kp_b_uri'],
                        'relation_type': 'PREREQUISITE',
                        'confidence': min(existing['confidence'] + 0.1, 1.0),
                        'source': 'multi_evidence',
                        'reason': f"{existing['source']} + llm_vote"
                    }

        # 转换为列表
        results = list(fused.values())

        # 统计
        stats = {}
        for r in results:
            rt = r['relation_type']
            stats[rt] = stats.get(rt, 0) + 1

        logger.info(f"融合完成: {stats}")

        return results


def estimate_inference_cost(kp_count: int) -> Dict[str, Any]:
    """
    估算推断成本

    Args:
        kp_count: 知识点数量

    Returns:
        成本估算信息
    """
    # 假设每个知识点与其他知识点平均有 2 个潜在前置关系
    pair_count = kp_count * 2

    # 每个知识点对调用 2 个模型
    llm_calls = pair_count * 2

    # GLM-4-flash 免费，DeepSeek 成本估算
    deepseek_cost = llm_calls / 2 * 0.001 / 1000  # 约 0.001 元/1000 tokens

    return {
        'kp_count': kp_count,
        'estimated_pairs': pair_count,
        'llm_calls': llm_calls,
        'glm_calls': llm_calls // 2,
        'deepseek_calls': llm_calls // 2,
        'estimated_cost_rmb': deepseek_cost,
        'note': 'GLM-4-flash 免费，DeepSeek 约 0.001元/1000 tokens'
    }