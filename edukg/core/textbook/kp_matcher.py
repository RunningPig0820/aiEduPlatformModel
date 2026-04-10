"""
知识点匹配器

复用 edukg/core/llm_inference 双模型投票机制进行知识点匹配。
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any

from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt
from edukg.core.llm_inference.dual_model_voter import vote_with_retry

logger = logging.getLogger(__name__)


class KPMatcher:
    """
    知识点匹配器

    使用双模型投票机制匹配教材知识点到图谱知识点。

    使用方法:
        matcher = KPMatcher()
        results = await matcher.match_all(textbook_kps, kg_concepts)
    """

    def __init__(self, voter: DualModelVoter = None):
        """
        初始化知识点匹配器

        Args:
            voter: DualModelVoter 实例（可选，默认创建新实例）
        """
        self.voter = voter or DualModelVoter()

    def exact_match(
        self,
        textbook_kp_name: str,
        kg_concepts: List[Dict]
    ) -> Optional[Dict]:
        """
        精确匹配

        检查教材知识点名称是否与图谱知识点名称完全一致。

        Args:
            textbook_kp_name: 教材知识点名称
            kg_concepts: 图谱知识点列表，格式为 [{'uri': ..., 'label': ...}, ...]

        Returns:
            匹配结果或 None
        """
        for concept in kg_concepts:
            if concept.get('label') == textbook_kp_name:
                return {
                    'kg_uri': concept['uri'],
                    'kg_name': concept['label'],
                    'confidence': 1.0,
                    'method': 'exact_match'
                }
        return None

    async def llm_match(
        self,
        textbook_kp: Dict,
        kg_concepts: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """
        LLM 语义匹配

        使用双模型投票判断教材知识点与图谱知识点的语义相似度。

        Args:
            textbook_kp: 教材知识点，格式为 {'uri': ..., 'label': ..., 'stage': ..., 'grade': ...}
            kg_concepts: 图谱知识点列表
            top_k: 返回前 K 个匹配结果

        Returns:
            匹配结果列表，格式为 [{'kg_uri': ..., 'confidence': 0.9, 'method': 'llm_vote'}, ...]
        """
        results = []
        textbook_kp_name = textbook_kp.get('label', '')
        textbook_kp_desc = f"学段: {textbook_kp.get('stage', '')}, 年级: {textbook_kp.get('grade', '')}"

        # 对每个候选图谱知识点进行匹配
        for concept in kg_concepts:
            kg_kp_name = concept.get('label', '')
            kg_kp_desc = concept.get('description', '')

            # 格式化 Prompt
            prompt = format_kp_match_prompt(
                textbook_kp_name=textbook_kp_name,
                textbook_kp_description=textbook_kp_desc,
                kg_kp_name=kg_kp_name,
                kg_kp_description=kg_kp_desc or "无描述"
            )

            # 执行投票
            vote_result = await vote_with_retry(self.voter, prompt)

            if vote_result['consensus']:
                result = vote_result['result']
                decision = result.get('decision', False)
                confidence = result.get('confidence', 0.0)

                if decision:
                    results.append({
                        'textbook_kp_uri': textbook_kp['uri'],
                        'textbook_kp_name': textbook_kp_name,
                        'kg_uri': concept['uri'],
                        'kg_name': kg_kp_name,
                        'confidence': confidence,
                        'method': 'llm_vote',
                        'reason': result.get('primary_reason', '')
                    })

        # 按置信度排序，返回 top_k
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results[:top_k]

    async def match_all(
        self,
        textbook_kps: List[Dict],
        kg_concepts: List[Dict],
        use_llm: bool = True,
        progress_callback: callable = None
    ) -> List[Dict]:
        """
        批量匹配所有知识点

        Args:
            textbook_kps: 教材知识点列表
            kg_concepts: 图谱知识点列表
            use_llm: 是否使用 LLM 匹配（默认 True）
            progress_callback: 进度回调函数

        Returns:
            匹配结果列表
        """
        results = []
        total = len(textbook_kps)

        logger.info(f"开始匹配 {total} 个教材知识点")

        for i, kp in enumerate(textbook_kps):
            # 进度回调
            if progress_callback:
                progress_callback(i + 1, total, kp.get('label', ''))

            # 显示进度
            if (i + 1) % 10 == 0 or i == 0:
                logger.info(f"进度: {i + 1}/{total} ({(i + 1) / total * 100:.1f}%)")

            # 1. 先尝试精确匹配
            match = self.exact_match(kp.get('label', ''), kg_concepts)

            if match:
                results.append({
                    'textbook_kp_uri': kp['uri'],
                    'textbook_kp_name': kp['label'],
                    'kg_uri': match['kg_uri'],
                    'kg_name': match['kg_name'],
                    'confidence': match['confidence'],
                    'method': 'exact_match'
                })
            elif use_llm:
                # 2. 精确匹配失败，使用 LLM 匹配
                # 筛选候选：可以添加启发式规则缩小范围
                llm_results = await self.llm_match(kp, kg_concepts, top_k=1)
                results.extend(llm_results)

        # 统计
        exact_count = sum(1 for r in results if r['method'] == 'exact_match')
        llm_count = sum(1 for r in results if r['method'] == 'llm_vote')

        logger.info(f"匹配完成: 精确匹配={exact_count}, LLM匹配={llm_count}, 未匹配={total - len(results)}")

        return results

    def save_results(self, results: List[Dict], filepath: str):
        """
        保存匹配结果

        Args:
            results: 匹配结果列表
            filepath: 文件路径
        """
        import json
        from pathlib import Path

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"保存匹配结果: {filepath} ({len(results)} 条)")


def estimate_match_cost(textbook_kp_count: int) -> Dict[str, Any]:
    """
    估算匹配成本

    Args:
        textbook_kp_count: 教材知识点数量

    Returns:
        成本估算信息
    """
    # 假设精确匹配率 10%，剩余 90% 需要 LLM 匹配
    exact_match_count = int(textbook_kp_count * 0.1)
    llm_match_count = textbook_kp_count - exact_match_count

    # 每个 LLM 匹配需要对多个候选进行投票
    # 假设每个知识点平均比较 5 个候选
    llm_calls = llm_match_count * 5 * 2  # * 2 因为双模型

    # GLM-4-flash 免费，DeepSeek 成本
    deepseek_cost = llm_calls / 2 * 0.001 / 1000

    return {
        'textbook_kp_count': textbook_kp_count,
        'estimated_exact_match': exact_match_count,
        'estimated_llm_match': llm_match_count,
        'llm_calls': llm_calls,
        'estimated_cost_rmb': deepseek_cost,
        'note': 'GLM-4-flash 免费，DeepSeek 约 0.001元/1000 tokens'
    }