"""
知识点匹配器

复用 edukg/core/llm_inference 双模型投票机制进行知识点匹配。
支持断点续传和 LLM 调用缓存。
"""
import asyncio
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt
from edukg.core.llm_inference.dual_model_voter import vote_with_retry
from edukg.core.llmTaskLock import TaskState, ProcessLock, get_cache_key, save_cache, load_cache

logger = logging.getLogger(__name__)

# 进度文件目录
PROGRESS_DIR = Path(__file__).parent.parent.parent / "data" / "edukg" / "math" / "5_教材目录(Textbook)" / "output" / "progress"


class KPMatcher:
    """
    知识点匹配器

    使用双模型投票机制匹配教材知识点到图谱知识点。
    支持断点续传和 LLM 调用缓存。

    使用方法:
        matcher = KPMatcher()
        results = await matcher.match_all(textbook_kps, kg_concepts, resume=True)
    """

    def __init__(
        self,
        voter: DualModelVoter = None,
        progress_dir: Path = None,
        cache_dir: Path = None
    ):
        """
        初始化知识点匹配器

        Args:
            voter: DualModelVoter 实例（可选，默认创建新实例）
            progress_dir: 进度文件目录
            cache_dir: LLM 缓存目录
        """
        self.voter = voter or DualModelVoter()
        self.progress_dir = progress_dir or PROGRESS_DIR
        self.cache_dir = cache_dir or (self.progress_dir.parent / "llm_cache")

        # 确保目录存在
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 任务状态管理
        self.task_state = TaskState(
            "match_kg",
            state_dir=self.progress_dir
        )

        # 进程锁
        self.process_lock = ProcessLock(
            str(self.progress_dir / "match_kg.lock")
        )

    def _make_pair_id(self, textbook_kp_uri: str, kg_uri: str) -> str:
        """
        生成知识点对 ID

        Args:
            textbook_kp_uri: 教材知识点 URI
            kg_uri: 图谱知识点 URI

        Returns:
            唯一的 ID 字符串
        """
        combined = f"{textbook_kp_uri}||{kg_uri}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]

    def _get_cached_result(self, prompt: str) -> Optional[Dict]:
        """
        获取缓存的 LLM 结果

        Args:
            prompt: 提示词

        Returns:
            缓存的结果或 None
        """
        cache_key = get_cache_key(prompt)
        return load_cache(cache_key, self.cache_dir)

    def _save_cached_result(self, prompt: str, result: Dict):
        """
        保存 LLM 结果到缓存

        Args:
            prompt: 提示词
            result: 结果数据
        """
        cache_key = get_cache_key(prompt)
        save_cache(cache_key, result, self.cache_dir, prompt=prompt)

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
        resume: bool = True,
        progress_callback: callable = None,
        checkpoint_interval: int = 10
    ) -> List[Dict]:
        """
        批量匹配所有知识点

        Args:
            textbook_kps: 教材知识点列表
            kg_concepts: 图谱知识点列表
            use_llm: 是否使用 LLM 匹配（默认 True）
            resume: 是否支持断点续传（默认 True）
            progress_callback: 进度回调函数
            checkpoint_interval: 每 N 个知识点保存一次进度

        Returns:
            匹配结果列表
        """
        results = []
        total = len(textbook_kps)

        # 加载已完成的知识点
        completed_uris: Set[str] = set()
        if resume:
            state = self.task_state.get_state()
            for checkpoint in state.get('checkpoints', []):
                if checkpoint.get('status') == 'completed':
                    # 从结果中恢复
                    result_data = checkpoint.get('result')
                    if result_data:
                        results.append(result_data)
                        completed_uris.add(result_data.get('textbook_kp_uri'))

        # 筛选待处理的知识点
        pending_kps = [kp for kp in textbook_kps if kp.get('uri') not in completed_uris]

        if pending_kps:
            logger.info(f"开始匹配 {total} 个教材知识点，已完成 {len(completed_uris)}，待处理 {len(pending_kps)}")
        else:
            logger.info(f"所有 {total} 个知识点已匹配完成")
            return results

        # 初始化任务状态
        if not self.task_state.is_completed():
            self.task_state.start(total=len(pending_kps))

        # 使用进程锁保护
        with self.process_lock:
            processed_count = 0

            for kp in pending_kps:
                kp_uri = kp.get('uri', '')

                # 进度回调
                if progress_callback:
                    progress_callback(len(results) + 1, total, kp.get('label', ''))

                # 显示进度
                processed_count += 1
                if processed_count % checkpoint_interval == 0 or processed_count == 1:
                    logger.info(f"进度: {processed_count}/{len(pending_kps)} ({processed_count / len(pending_kps) * 100:.1f}%)")

                # 1. 先尝试精确匹配
                match = self.exact_match(kp.get('label', ''), kg_concepts)

                if match:
                    result = {
                        'textbook_kp_uri': kp['uri'],
                        'textbook_kp_name': kp['label'],
                        'kg_uri': match['kg_uri'],
                        'kg_name': match['kg_name'],
                        'confidence': match['confidence'],
                        'method': 'exact_match'
                    }
                    results.append(result)

                    # 记录完成
                    checkpoint_id = f"kp_{kp_uri.split('#')[-1]}"
                    self.task_state.complete_checkpoint(checkpoint_id, result)

                elif use_llm:
                    # 2. 精确匹配失败，使用 LLM 匹配
                    llm_results = await self.llm_match_with_cache(
                        kp, kg_concepts, top_k=1
                    )
                    results.extend(llm_results)

                    # 记录完成
                    if llm_results:
                        checkpoint_id = f"kp_{kp_uri.split('#')[-1]}"
                        self.task_state.complete_checkpoint(checkpoint_id, llm_results[0])

                # 定期保存进度
                if processed_count % checkpoint_interval == 0:
                    self.task_state._save_state()

            # 最终保存
            self.task_state._save_state()

        # 统计
        exact_count = sum(1 for r in results if r['method'] == 'exact_match')
        llm_count = sum(1 for r in results if r['method'] == 'llm_vote')

        logger.info(f"匹配完成: 精确匹配={exact_count}, LLM匹配={llm_count}, 未匹配={total - len(results)}")

        return results

    async def llm_match_with_cache(
        self,
        textbook_kp: Dict,
        kg_concepts: List[Dict],
        top_k: int = 3
    ) -> List[Dict]:
        """
        LLM 语义匹配（带缓存）

        使用双模型投票判断教材知识点与图谱知识点的语义相似度。
        优先使用缓存结果。

        Args:
            textbook_kp: 教材知识点
            kg_concepts: 图谱知识点列表
            top_k: 返回前 K 个匹配结果

        Returns:
            匹配结果列表
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

            # 检查缓存
            cached_result = self._get_cached_result(prompt)
            if cached_result:
                # 使用缓存结果
                if cached_result.get('consensus') and cached_result.get('result', {}).get('decision'):
                    result = cached_result['result']
                    results.append({
                        'textbook_kp_uri': textbook_kp['uri'],
                        'textbook_kp_name': textbook_kp_name,
                        'kg_uri': concept['uri'],
                        'kg_name': kg_kp_name,
                        'confidence': result.get('confidence', 0.0),
                        'method': 'llm_vote',
                        'reason': result.get('primary_reason', ''),
                        'from_cache': True
                    })
                continue

            # 执行投票
            vote_result = await vote_with_retry(self.voter, prompt)

            # 保存到缓存
            self._save_cached_result(prompt, vote_result)

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