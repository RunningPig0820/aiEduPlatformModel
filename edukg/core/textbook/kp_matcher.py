"""
知识点匹配器

复用 edukg/core/llm_inference 双模型投票机制进行知识点匹配。
支持断点续传和 LLM 调用缓存。

改进（采纳 DeepSeek 建议）:
1. 粗筛机制：先用向量检索筛选 top-N 候选，避免遍历所有图谱知识点
2. 精确匹配标准化：名称标准化 + 同义词映射
3. 异常处理：LLM调用失败继续下一个候选
4. 未匹配记录：输出所有知识点，增加 matched 字段
5. 向量检索：使用本地 Embedding 模型进行语义粗筛（可选）
"""
import asyncio
import json
import logging
import hashlib
import re
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable
from difflib import SequenceMatcher

from edukg.core.llm_inference import DualModelVoter
from edukg.core.llm_inference.prompt_templates import format_kp_match_prompt
from edukg.core.llm_inference.dual_model_voter import vote_with_retry
from edukg.core.llmTaskLock import TaskState, ProcessLock, get_cache_key, save_cache, load_cache

logger = logging.getLogger(__name__)

# 进度文件目录
PROGRESS_DIR = Path(__file__).parent.parent.parent / "data" / "edukg" / "math" / "5_教材目录(Textbook)" / "output" / "progress"

# 同义词映射表（向量检索模式下作为备用）
SYNONYM_MAP = {
    # 加法相关
    "加法": ["加", "加法运算", "相加", "求和"],
    "减法": ["减", "减法运算", "相减", "求差"],
    "乘法": ["乘", "乘法运算", "相乘", "求积"],
    "除法": ["除", "除法运算", "相除", "求商"],
    # 数的概念
    "百分数": ["百分比", "百分率"],
    "小数": ["小数数", "小数概念"],
    "分数": ["分数概念", "分数意义"],
    # 图形相关
    "三角形": ["三角形图形"],
    "正方形": ["正方形图形"],
    "长方形": ["矩形", "长方形图形"],
    # 其他常见同义词
    "方程": ["方程式"],
    "函数": ["函数概念"],
    "比例": ["比例关系"],
    "统计": ["统计学", "统计图表"],
}


class LocalVectorRetriever:
    """
    本地向量检索器

    使用 sentence-transformers 模型将知识点转换为向量，
    通过余弦相似度快速找到语义最接近的候选。

    特点：
    - 本地运行，无需 API 调用
    - 中文语义理解强（bge-small-zh-v1.5）
    - 内存占用约 3.5GB
    - 单次检索 < 10ms
    """

    def __init__(self, kg_concepts: List[Dict], model_name: str = "BAAI/bge-small-zh-v1.5"):
        """
        初始化向量检索器

        Args:
            kg_concepts: 图谱知识点列表
            model_name: Embedding 模型名称
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "请安装 sentence-transformers: pip install sentence-transformers"
            )

        logger.info(f"加载向量检索模型: {model_name}")
        self.model = SentenceTransformer(model_name)

        # 构建知识点文本（label + description）
        self.concepts = kg_concepts
        self.texts = [
            f"{c.get('label', '')} {c.get('description', '')}"
            for c in kg_concepts
        ]

        # 预计算所有图谱知识点的向量
        logger.info(f"预计算 {len(kg_concepts)} 个图谱知识点的向量...")
        self.vectors = self.model.encode(
            self.texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # 归一化向量（用于余弦相似度）
        self.vectors = self.vectors / np.linalg.norm(self.vectors, axis=1, keepdims=True)

        logger.info(f"向量检索器初始化完成，向量维度: {self.vectors.shape}")

    def retrieve(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        检索语义最接近的候选

        Args:
            query: 查询文本（教材知识点名称）
            top_k: 返回候选数量

        Returns:
            候选知识点列表
        """
        # 编码查询向量
        query_vec = self.model.encode([query], convert_to_numpy=True)[0]
        query_vec = query_vec / np.linalg.norm(query_vec)

        # 计算余弦相似度（向量已归一化，直接 dot 即可）
        scores = np.dot(self.vectors, query_vec)

        # 取 top-k
        top_idx = np.argsort(scores)[-top_k:][::-1]

        return [self.concepts[i] for i in top_idx]


class KPMatcher:
    """
    知识点匹配器

    使用双模型投票机制匹配教材知识点到图谱知识点。
    支持断点续传和 LLM 调用缓存。

    粗筛方式：
    - 向量检索（默认）：使用本地 Embedding 模型进行语义匹配
    - difflib（备用）：字符相似度匹配

    使用方法:
        matcher = KPMatcher(use_vector_retrieval=True)
        results = await matcher.match_all(textbook_kps, kg_concepts, resume=True)
    """

    def __init__(
        self,
        voter: DualModelVoter = None,
        progress_dir: Path = None,
        cache_dir: Path = None,
        candidate_top_n: int = 20,
        use_vector_retrieval: bool = True
    ):
        """
        初始化知识点匹配器

        Args:
            voter: DualModelVoter 实例（可选，默认创建新实例）
            progress_dir: 进度文件目录
            cache_dir: LLM 缓存目录
            candidate_top_n: 粗筛候选数量（默认20）
            use_vector_retrieval: 是否使用向量检索（默认True）
        """
        self.voter = voter or DualModelVoter()
        self.progress_dir = progress_dir or PROGRESS_DIR
        self.cache_dir = cache_dir or (self.progress_dir.parent / "llm_cache")
        self.candidate_top_n = candidate_top_n
        self.use_vector_retrieval = use_vector_retrieval

        # 向量检索器（懒加载，在 match_all 时初始化）
        self.vector_retriever = None

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

        # 统计信息
        self.stats = {
            'exact_match': 0,
            'llm_match': 0,
            'unmatched': 0,
            'errors': 0,
            'cache_hits': 0,
        }

    def _init_vector_retriever(self, kg_concepts: List[Dict]):
        """
        初始化向量检索器（懒加载）

        Args:
            kg_concepts: 图谱知识点列表
        """
        if not self.use_vector_retrieval:
            return

        if self.vector_retriever is not None:
            return

        try:
            logger.info("初始化向量检索器...")
            self.vector_retriever = LocalVectorRetriever(kg_concepts)
            logger.info("向量检索器初始化成功")
        except ImportError as e:
            logger.warning(f"向量检索器初始化失败（依赖缺失）: {e}")
            logger.warning("回退到 difflib 粗筛模式")
            self.use_vector_retrieval = False
        except Exception as e:
            logger.warning(f"向量检索器初始化失败: {e}")
            logger.warning("回退到 difflib 粗筛模式")
            self.use_vector_retrieval = False

    def _normalize_name(self, name: str) -> str:
        """
        标准化知识点名称

        处理：大小写、空格、全半角括号等

        Args:
            name: 知识点名称

        Returns:
            标准化后的名称
        """
        if not name:
            return ""
        # 转小写、去空格、统一括号
        normalized = name.strip().lower()
        normalized = normalized.replace(' ', '').replace('　', '')  # 半角/全角空格
        normalized = normalized.replace('（', '(').replace('）', ')')
        normalized = normalized.replace('【', '[').replace('】', ']')
        return normalized

    def _expand_with_synonyms(self, name: str) -> List[str]:
        """
        扩展同义词（完整词匹配，防止过度匹配）

        改进：只在精确匹配时使用完整词匹配，避免"加法交换律"匹配到"加法"

        Args:
            name: 知识点名称

        Returns:
            包含原名称和所有同义词的列表
        """
        names = [name]
        normalized_name = self._normalize_name(name)

        # 完整词匹配：只查找完全匹配的同义词
        for key, synonyms in SYNONYM_MAP.items():
            normalized_key = self._normalize_name(key)
            # 完整匹配（不是部分包含）
            if normalized_name == normalized_key or name == key:
                names.extend(synonyms)
                names.append(key)

        # 反向查找：name 可能是某个同义词的完整匹配
        for key, synonyms in SYNONYM_MAP.items():
            for syn in synonyms:
                normalized_syn = self._normalize_name(syn)
                if normalized_name == normalized_syn or name == syn:
                    names.append(key)
                    names.extend([s for s in synonyms if s != name])

        # 去重
        return list(set(names))

    def exact_match(
        self,
        textbook_kp_name: str,
        kg_concepts: List[Dict]
    ) -> Optional[Dict]:
        """
        精确匹配（带标准化和同义词）

        Args:
            textbook_kp_name: 教材知识点名称
            kg_concepts: 图谱知识点列表

        Returns:
            匹配结果或 None
        """
        # 扩展同义词
        search_names = self._expand_with_synonyms(textbook_kp_name)
        normalized_search = [self._normalize_name(n) for n in search_names]

        for concept in kg_concepts:
            kg_name = concept.get('label', '')
            normalized_kg = self._normalize_name(kg_name)

            # 检查是否匹配（标准化后比较）
            if normalized_kg in normalized_search:
                return {
                    'kg_uri': concept['uri'],
                    'kg_name': kg_name,
                    'confidence': 1.0,
                    'method': 'exact_match',
                    'matched_variant': kg_name  # 记录匹配的变体
                }

            # 原名称直接匹配
            if kg_name in search_names:
                return {
                    'kg_uri': concept['uri'],
                    'kg_name': kg_name,
                    'confidence': 1.0,
                    'method': 'exact_match'
                }

        return None

    def _retrieve_candidates(
        self,
        textbook_kp_name: str,
        kg_concepts: List[Dict],
        top_n: int = None
    ) -> List[Dict]:
        """
        粗筛：基于文本相似度或向量检索筛选候选

        优先使用向量检索（语义匹配），若不可用则回退到 difflib（字符匹配）。

        Args:
            textbook_kp_name: 教材知识点名称
            kg_concepts: 图谱知识点列表
            top_n: 返回候选数量（默认使用 self.candidate_top_n）

        Returns:
            候选列表
        """
        top_n = top_n or self.candidate_top_n

        # 优先使用向量检索（语义匹配）
        if self.use_vector_retrieval and self.vector_retriever is not None:
            return self.vector_retriever.retrieve(textbook_kp_name, top_n)

        # 回退：difflib 字符相似度匹配
        normalized_input = self._normalize_name(textbook_kp_name)

        scores = []
        for concept in kg_concepts:
            kg_name = concept.get('label', '')
            normalized_kg = self._normalize_name(kg_name)

            # 计算相似度
            similarity = SequenceMatcher(None, normalized_input, normalized_kg).ratio()

            # 如果名称包含关系，额外加分
            if normalized_input in normalized_kg or normalized_kg in normalized_input:
                similarity += 0.2

            scores.append((similarity, concept))

        # 排序取 top-N
        scores.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scores[:top_n]]

    def _get_cached_result(self, prompt: str) -> Optional[Dict]:
        """获取缓存的 LLM 结果"""
        cache_key = get_cache_key(prompt)
        return load_cache(cache_key, self.cache_dir)

    def _save_cached_result(self, prompt: str, result: Dict):
        """保存 LLM 结果到缓存"""
        cache_key = get_cache_key(prompt)
        save_cache(cache_key, result, self.cache_dir, prompt=prompt)

    async def llm_match_with_cache(
        self,
        textbook_kp: Dict,
        kg_concepts: List[Dict],
        top_k: int = 1
    ) -> List[Dict]:
        """
        LLM 语义匹配（带缓存和粗筛）

        改进：
        1. 先粗筛 top-N 候选，避免遍历所有图谱知识点
        2. 异常处理：LLM调用失败继续下一个候选

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

        # 1. 粗筛：只对 top-N 候选进行 LLM 匹配
        candidates = self._retrieve_candidates(textbook_kp_name, kg_concepts, self.candidate_top_n)

        logger.debug(f"粗筛结果: {textbook_kp_name} -> {len(candidates)} 个候选")

        # 2. 对每个候选进行 LLM 投票
        for concept in candidates:
            kg_kp_name = concept.get('label', '')
            kg_kp_desc = concept.get('description', '')

            # 格式化 Prompt
            prompt = format_kp_match_prompt(
                textbook_kp_name=textbook_kp_name,
                textbook_kp_description=textbook_kp_desc,
                kg_kp_name=kg_kp_name,
                kg_kp_description=kg_kp_desc or "无描述"
            )

            try:
                # 检查缓存
                cached_result = self._get_cached_result(prompt)
                if cached_result:
                    self.stats['cache_hits'] += 1
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

            except Exception as e:
                self.stats['errors'] += 1
                logger.warning(f"LLM调用失败: {textbook_kp_name} -> {kg_kp_name}, 错误: {e}")
                continue  # 继续下一个候选

        # 按置信度排序，返回 top_k
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results[:top_k]

    async def match_all(
        self,
        textbook_kps: List[Dict],
        kg_concepts: List[Dict],
        use_llm: bool = True,
        resume: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        checkpoint_interval: int = 10
    ) -> List[Dict]:
        """
        批量匹配所有知识点

        改进：
        1. 输出所有知识点，增加 matched 字段
        2. 使用 processed_count 作为进度

        Args:
            textbook_kps: 教材知识点列表
            kg_concepts: 图谱知识点列表
            use_llm: 是否使用 LLM 匹配（默认 True）
            resume: 是否支持断点续传（默认 True）
            progress_callback: 进度回调函数
            checkpoint_interval: 每 N 个知识点保存一次进度

        Returns:
            匹配结果列表（包含未匹配的知识点，带 matched 字段）
        """
        results = []
        total = len(textbook_kps)

        # 重置统计
        self.stats = {
            'exact_match': 0,
            'llm_match': 0,
            'unmatched': 0,
            'errors': 0,
            'cache_hits': 0,
        }

        # 初始化向量检索器（懒加载）
        self._init_vector_retriever(kg_concepts)

        # 加载已完成的知识点
        completed_uris: Set[str] = set()
        if resume:
            state = self.task_state.get_state()
            for checkpoint in state.get('checkpoints', []):
                if checkpoint.get('status') == 'completed':
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
                kp_name = kp.get('label', '')
                processed_count += 1

                # 显示进度（含已恢复的结果）
                completed_total = len(results) + 1  # 包含正在处理的这一个
                if processed_count % checkpoint_interval == 0 or processed_count == 1:
                    logger.info(f"进度: {completed_total}/{total} ({completed_total / total * 100:.1f}%) - {kp_name}")

                # 进度回调（使用实际已完成数量）
                if progress_callback:
                    progress_callback(completed_total, total, kp_name)

                # 1. 先尝试精确匹配
                match = self.exact_match(kp_name, kg_concepts)

                if match:
                    result = {
                        'textbook_kp_uri': kp_uri,
                        'textbook_kp_name': kp_name,
                        'kg_uri': match['kg_uri'],
                        'kg_name': match['kg_name'],
                        'confidence': match['confidence'],
                        'method': 'exact_match',
                        'matched': True
                    }
                    results.append(result)
                    self.stats['exact_match'] += 1

                    # 记录完成
                    checkpoint_id = f"kp_{kp_uri.split('#')[-1]}"
                    self.task_state.complete_checkpoint(checkpoint_id, result)

                elif use_llm:
                    # 2. 精确匹配失败，使用 LLM 匹配（粗筛 + 缓存）
                    llm_results = await self.llm_match_with_cache(kp, kg_concepts, top_k=1)

                    if llm_results:
                        # 匹配成功
                        llm_results[0]['matched'] = True
                        results.extend(llm_results)
                        self.stats['llm_match'] += 1

                        checkpoint_id = f"kp_{kp_uri.split('#')[-1]}"
                        self.task_state.complete_checkpoint(checkpoint_id, llm_results[0])
                    else:
                        # 未匹配
                        result = {
                            'textbook_kp_uri': kp_uri,
                            'textbook_kp_name': kp_name,
                            'kg_uri': None,
                            'kg_name': None,
                            'confidence': 0.0,
                            'method': 'none',
                            'matched': False,
                            'reason': 'LLM匹配失败，无候选通过'
                        }
                        results.append(result)
                        self.stats['unmatched'] += 1

                        checkpoint_id = f"kp_{kp_uri.split('#')[-1]}"
                        self.task_state.complete_checkpoint(checkpoint_id, result)

                else:
                    # 不使用 LLM，直接标记未匹配
                    result = {
                        'textbook_kp_uri': kp_uri,
                        'textbook_kp_name': kp_name,
                        'kg_uri': None,
                        'kg_name': None,
                        'confidence': 0.0,
                        'method': 'none',
                        'matched': False,
                        'reason': '精确匹配失败，LLM未启用'
                    }
                    results.append(result)
                    self.stats['unmatched'] += 1

                # 定期保存进度
                if processed_count % checkpoint_interval == 0:
                    self.task_state._save_state()

            # 最终保存
            self.task_state._save_state()

        # 统计报告
        logger.info(f"\n=== 匹配完成 ===")
        logger.info(f"精确匹配: {self.stats['exact_match']}")
        logger.info(f"LLM匹配: {self.stats['llm_match']} (缓存命中: {self.stats['cache_hits']})")
        logger.info(f"未匹配: {self.stats['unmatched']}")
        logger.info(f"LLM错误: {self.stats['errors']}")
        logger.info(f"匹配率: {(self.stats['exact_match'] + self.stats['llm_match']) / total * 100:.1f}%")

        return results

    def save_results(self, results: List[Dict], filepath: str):
        """保存匹配结果"""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"保存匹配结果: {filepath} ({len(results)} 条)")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()


def estimate_match_cost(
    textbook_kp_count: int,
    exact_match_rate: float = 0.15,
    avg_candidates: int = 20
) -> Dict[str, Any]:
    """
    估算匹配成本（改进版）

    Args:
        textbook_kp_count: 教材知识点数量
        exact_match_rate: 精确匹配率（默认15%，因为有同义词扩展）
        avg_candidates: 每个LLM匹配的候选数量（默认20，使用粗筛）

    Returns:
        成本估算信息
    """
    exact_match_count = int(textbook_kp_count * exact_match_rate)
    llm_match_count = textbook_kp_count - exact_match_count

    # 每个 LLM 匹配只比较粗筛后的候选（不再是全量）
    llm_calls = llm_match_count * avg_candidates * 2  # * 2 因为双模型

    # GLM-4-flash 免费，DeepSeek 成本
    deepseek_cost = llm_calls / 2 * 0.001 / 1000

    return {
        'textbook_kp_count': textbook_kp_count,
        'estimated_exact_match': exact_match_count,
        'estimated_llm_match': llm_match_count,
        'llm_calls': llm_calls,
        'avg_candidates_per_kp': avg_candidates,
        'estimated_cost_rmb': deepseek_cost,
        'note': f'使用粗筛（top-{avg_candidates}候选），GLM-4-flash 免费'
    }