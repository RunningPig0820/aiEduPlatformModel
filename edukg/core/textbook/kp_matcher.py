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
6. 并发处理：使用 Semaphore + gather 并发匹配（可选）
7. 并发安全：asyncio.Lock 保护 + 处理中状态检查
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
from edukg.core.textbook.config import VECTOR_INDEX_DIR

logger = logging.getLogger(__name__)

# 进度文件目录
PROGRESS_DIR = Path(__file__).parent.parent.parent / "data" / "edukg" / "math" / "5_教材目录(Textbook)" / "output" / "progress"

# 标准化结果文件
NORMALIZED_KPS_FILE = Path(__file__).parent.parent.parent / "data" / "edukg" / "math" / "5_教材目录(Textbook)" / "output" / "normalized_kps_complete.json"

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

        # 设置离线模式，避免每次启动都联网检查更新
        import os
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

        logger.info(f"加载向量检索模型: {model_name} (离线模式)")
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
            候选知识点列表（含 score 相似度）
        """
        # 编码查询向量
        query_vec = self.model.encode([query], convert_to_numpy=True)[0]
        query_vec = query_vec / np.linalg.norm(query_vec)

        # 计算余弦相似度
        scores = np.dot(self.vectors, query_vec)

        # 取 top-k
        top_idx = np.argsort(scores)[-top_k:][::-1]

        # 返回候选（含相似度分数）
        results = []
        for i in top_idx:
            concept = self.concepts[i].copy()
            concept['score'] = float(scores[i])
            results.append(concept)
        return results


class PrebuiltIndexRetriever:
    """
    预构建索引检索器

    使用预先构建的向量索引进行检索，无需加载模型。
    适合多次运行的匹配脚本，启动更快。

    特点：
    - 加载快（仅需加载 numpy 文件）
    - 无需模型（内存占用约 10MB）
    - 单次检索 < 5ms
    """

    def __init__(
        self,
        vectors: np.ndarray,
        texts: List[str],
        concepts: List[Dict],
        model_name: str = "BAAI/bge-small-zh-v1.5"
    ):
        """
        初始化预构建索引检索器

        Args:
            vectors: 预计算的向量矩阵 (N, 512)
            texts: 知识点文本列表
            concepts: 知识点元数据列表
            model_name: 原模型名称（用于后续查询编码）
        """
        self.vectors = vectors
        self.texts = texts
        self.concepts = concepts
        self.model_name = model_name

        # 设置离线模式，避免每次启动都联网检查更新
        import os
        # 强制离线模式，避免联网检查更新（首次已下载好模型）
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        # 加载模型用于查询编码
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"加载查询编码模型: {model_name} (离线模式)")
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError(
                "请安装 sentence-transformers: pip install sentence-transformers"
            )

        # 归一化向量
        self.vectors = self.vectors / np.linalg.norm(self.vectors, axis=1, keepdims=True)

        logger.info(f"预构建索引检索器初始化完成，知识点数: {len(concepts)}")

    def retrieve(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        检索语义最接近的候选

        Args:
            query: 查询文本（教材知识点名称）
            top_k: 返回候选数量

        Returns:
            候选知识点列表（含 score 相似度）
        """
        # 编码查询向量
        query_vec = self.model.encode([query], convert_to_numpy=True)[0]
        query_vec = query_vec / np.linalg.norm(query_vec)

        # 计算余弦相似度
        scores = np.dot(self.vectors, query_vec)

        # 取 top-k
        top_idx = np.argsort(scores)[-top_k:][::-1]

        # 返回候选（含相似度分数）
        results = []
        for i in top_idx:
            concept = self.concepts[i].copy()
            concept['score'] = float(scores[i])
            results.append(concept)
        return results


class KPMatcher:
    """
    知识点匹配器

    使用双模型投票机制匹配教材知识点到图谱知识点。
    支持断点续传和 LLM 调用缓存。

    粗筛方式：
    - 向量检索（默认）：使用本地 Embedding 模型进行语义匹配
    - difflib（备用）：字符相似度匹配

    索引加载方式：
    - 懒加载（默认）：每次运行时加载模型和构建向量
    - 预构建索引：加载预先构建的向量索引文件

    并发处理（新增）：
    - 使用 Semaphore 控制并发数
    - asyncio.Lock 保护缓存竞态
    - _processing_uris 防止重复处理

    使用方法:
        matcher = KPMatcher(use_vector_retrieval=True)
        results = await matcher.match_all(textbook_kps, kg_concepts, resume=True)

        # 使用预构建索引（更快启动）
        matcher = KPMatcher(use_prebuilt_index=True)
        results = await matcher.match_all(textbook_kps, kg_concepts, resume=True)

        # 并发处理（提速5x）
        matcher = KPMatcher(use_vector_retrieval=True)
        results = await matcher.match_all(textbook_kps, kg_concepts, max_concurrent=5)
    """

    # 并发安全：处理中的 URI 集合
    _processing_uris: Set[str] = set()
    _async_lock: asyncio.Lock = None  # 延迟初始化

    def __init__(
        self,
        voter: DualModelVoter = None,
        progress_dir: Path = None,
        cache_dir: Path = None,
        candidate_top_n: int = 20,
        use_vector_retrieval: bool = True,
        use_prebuilt_index: bool = False,
        prebuilt_index_path: Path = None
    ):
        """
        初始化知识点匹配器

        Args:
            voter: DualModelVoter 实例（可选，默认创建新实例）
            progress_dir: 进度文件目录
            cache_dir: LLM 缓存目录
            candidate_top_n: 粗筛候选数量（默认20）
            use_vector_retrieval: 是否使用向量检索（默认True）
            use_prebuilt_index: 是否使用预构建索引（默认False）
            prebuilt_index_path: 预构建索引目录（默认使用 config.VECTOR_INDEX_DIR）
        """
        self.voter = voter or DualModelVoter()
        self.progress_dir = progress_dir or PROGRESS_DIR
        self.cache_dir = cache_dir or (self.progress_dir.parent / "llm_cache")
        self.candidate_top_n = candidate_top_n
        self.use_vector_retrieval = use_vector_retrieval
        self.use_prebuilt_index = use_prebuilt_index
        self.prebuilt_index_path = prebuilt_index_path or VECTOR_INDEX_DIR

        # 向量检索器（懒加载，在 match_all 时初始化）
        self.vector_retriever = None

        # 预构建索引数据
        self.prebuilt_vectors = None
        self.prebuilt_texts = None
        self.prebuilt_concepts = None
        self.prebuilt_meta = None

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

        # 延迟初始化 asyncio.Lock（首次使用时创建）
        if KPMatcher._async_lock is None:
            KPMatcher._async_lock = asyncio.Lock()

        # 统计信息
        self.stats = {
            'exact_match': 0,
            'llm_match': 0,
            'unmatched': 0,
            'errors': 0,
            'cache_hits': 0,
        }

        # 标准化结果（懒加载）
        self._normalized_kps: Dict[str, Dict] = None  # 按教材名称索引
        self._use_normalized: bool = True  # 是否使用标准化结果

    def _load_normalized_kps(self) -> Dict[str, Dict]:
        """
        加载标准化结果（按教材名称索引）

        Returns:
            {教材名称: 标准化结果} 字典
        """
        if self._normalized_kps is not None:
            return self._normalized_kps

        if not NORMALIZED_KPS_FILE.exists():
            logger.warning(f"标准化结果文件不存在: {NORMALIZED_KPS_FILE}")
            self._normalized_kps = {}
            return self._normalized_kps

        with open(NORMALIZED_KPS_FILE, 'r', encoding='utf-8') as f:
            normalized_list = json.load(f)

        # 按 original（教材名称）索引
        self._normalized_kps = {}
        for item in normalized_list:
            original = item.get('original', '')
            if original:
                self._normalized_kps[original] = item

        logger.info(f"加载标准化结果: {len(self._normalized_kps)} 条")
        return self._normalized_kps

    def get_best_match(self, kp_name: str, stage: str = '', grade: str = '') -> str:
        """
        获取标准化后的最佳匹配名称

        Args:
            kp_name: 教材知识点名称
            stage: 学段（可选，用于更精确匹配）
            grade: 年级（可选）

        Returns:
            标准化后的概念名称，如果无标准化结果则返回原名称
        """
        if not self._use_normalized:
            return kp_name

        normalized = self._load_normalized_kps()

        # 尝试精确匹配
        if kp_name in normalized:
            return normalized[kp_name].get('best_match', kp_name)

        # 如果找不到，返回原名称
        return kp_name

    def get_normalized_info(self, kp_name: str) -> Optional[Dict]:
        """
        获取完整的标准化信息

        Args:
            kp_name: 教材知识点名称

        Returns:
            标准化结果字典，包含 concepts, best_match, confidence 等
        """
        normalized = self._load_normalized_kps()
        return normalized.get(kp_name)

    def load_vector_index(self, index_dir: Path = None) -> bool:
        """
        加载预构建向量索引

        Args:
            index_dir: 索引目录

        Returns:
            True 如果加载成功，False 如果失败
        """
        from edukg.core.textbook.vector_index_manager import VectorIndexManager

        index_dir = index_dir or self.prebuilt_index_path

        try:
            manager = VectorIndexManager()
            self.prebuilt_vectors, self.prebuilt_texts, self.prebuilt_concepts = manager.load_index(index_dir)
            self.prebuilt_meta = manager.meta

            logger.info(f"加载预构建索引成功:")
            logger.info(f"  模型: {self.prebuilt_meta.get('model_name')}")
            logger.info(f"  知识点数: {len(self.prebuilt_concepts)}")
            logger.info(f"  创建时间: {self.prebuilt_meta.get('created_at')}")

            return True

        except FileNotFoundError as e:
            logger.warning(f"预构建索引不存在: {index_dir}")
            logger.warning("请先运行 python build_vector_index.py 构建索引")
            return False

        except Exception as e:
            logger.warning(f"加载预构建索引失败: {e}")
            return False

    def check_index_validity(self, kg_concepts: List[Dict]) -> bool:
        """
        检查预构建索引是否有效

        Args:
            kg_concepts: 当前 Neo4j 中的知识点列表

        Returns:
            True 如果索引有效，False 如果过期
        """
        from edukg.core.textbook.vector_index_manager import VectorIndexManager

        if not self.prebuilt_meta:
            return False

        manager = VectorIndexManager()
        current_checksum = manager.get_checksum(kg_concepts)
        stored_checksum = self.prebuilt_meta.get("neo4j_checksum", "")

        if current_checksum != stored_checksum:
            logger.warning("⚠️  预构建索引已过期（checksum 不匹配）")
            logger.warning("图谱知识点已变化，建议运行 python build_vector_index.py --force 重建")
            return False

        return True

    def _init_vector_retriever(self, kg_concepts: List[Dict]):
        """
        初始化向量检索器（懒加载）

        改进：支持预构建索引加载

        Args:
            kg_concepts: 图谱知识点列表
        """
        if not self.use_vector_retrieval:
            return

        if self.vector_retriever is not None:
            return

        # 优先使用预构建索引
        if self.use_prebuilt_index:
            if self.load_vector_index():
                # 检查索引有效性
                if not self.check_index_validity(kg_concepts):
                    logger.warning("索引过期，回退到懒加载模式")
                    self.use_prebuilt_index = False
                else:
                    # 使用预构建索引创建检索器
                    self.vector_retriever = PrebuiltIndexRetriever(
                        self.prebuilt_vectors,
                        self.prebuilt_texts,
                        self.prebuilt_concepts,
                        self.prebuilt_meta.get("model_name", "BAAI/bge-small-zh-v1.5")
                    )
                    logger.info("使用预构建向量索引")
                    return
            else:
                # 加载失败，回退到懒加载
                logger.warning("预构建索引加载失败，回退到懒加载模式")
                self.use_prebuilt_index = False

        # 懒加载模式：每次运行时构建向量
        try:
            logger.info("初始化向量检索器（懒加载）...")
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
        kg_concepts: List[Dict],
        stage: str = '',
        grade: str = ''
    ) -> Optional[Dict]:
        """
        精确匹配（带标准化和同义词）

        改进：使用标准化后的 best_match 进行匹配，提高命中率

        Args:
            textbook_kp_name: 教材知识点名称
            kg_concepts: 图谱知识点列表
            stage: 学段（可选，用于更精确标准化）
            grade: 年级（可选）

        Returns:
            匹配结果或 None
        """
        # 1. 先获取标准化名称（用于向量检索）
        normalized_name = self.get_best_match(textbook_kp_name, stage, grade)

        # 2. 扩展同义词（同时包含原名称和标准化名称）
        search_names = self._expand_with_synonyms(textbook_kp_name)
        if normalized_name != textbook_kp_name:
            search_names.extend(self._expand_with_synonyms(normalized_name))
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
        top_n: int = None,
        stage: str = '',
        grade: str = ''
    ) -> List[Dict]:
        """
        粗筛：基于文本相似度或向量检索筛选候选

        优先使用向量检索（语义匹配），若不可用则回退到 difflib（字符匹配）。

        改进：使用标准化后的 best_match 进行向量检索，提高命中率

        Args:
            textbook_kp_name: 教材知识点名称
            kg_concepts: 图谱知识点列表
            top_n: 返回候选数量（默认使用 self.candidate_top_n）
            stage: 学段（可选）
            grade: 年级（可选）

        Returns:
            候选列表
        """
        top_n = top_n or self.candidate_top_n

        # 获取标准化名称（用于向量检索）
        normalized_name = self.get_best_match(textbook_kp_name, stage, grade)

        # 优先使用向量检索（语义匹配）
        if self.use_vector_retrieval and self.vector_retriever is not None:
            try:
                # 使用标准化名称进行检索（更准确）
                candidates = self.vector_retriever.retrieve(normalized_name, top_n)

                # 记录标准化信息（用于后续分析）
                if normalized_name != textbook_kp_name:
                    logger.debug(f"向量检索: '{textbook_kp_name}' → '{normalized_name}'")

                return candidates
            except Exception as e:
                logger.warning(f"向量检索失败: {e}, 回退到 difflib")
                # 继续使用 difflib 回退

        # 回退：difflib 字符相似度匹配（同时尝试原名称和标准化名称）
        search_names = [textbook_kp_name]
        if normalized_name != textbook_kp_name:
            search_names.append(normalized_name)

        normalized_inputs = [self._normalize_name(n) for n in search_names]

        scores = []
        for concept in kg_concepts:
            kg_name = concept.get('label', '')
            normalized_kg = self._normalize_name(kg_name)

            # 计算相似度（取最大值）
            max_similarity = 0
            for normalized_input in normalized_inputs:
                similarity = SequenceMatcher(None, normalized_input, normalized_kg).ratio()

                # 如果名称包含关系，额外加分
                if normalized_input in normalized_kg or normalized_kg in normalized_input:
                    similarity += 0.2

                max_similarity = max(max_similarity, similarity)

            scores.append((max_similarity, concept))

        # 排序取 top-N
        scores.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scores[:top_n]]

    async def _get_cached_result(self, prompt: str) -> Optional[Dict]:
        """
        获取缓存的 LLM 结果（并发安全）

        改进：加锁保护文件读取操作
        """
        cache_key = get_cache_key(prompt)
        # 加锁保护缓存读取（避免并发读写冲突）
        async with KPMatcher._async_lock:
            return load_cache(cache_key, self.cache_dir)

    async def _save_cached_result(self, prompt: str, result: Dict):
        """
        保存 LLM 结果到缓存（并发安全）

        改进：加锁保护文件写入操作
        """
        cache_key = get_cache_key(prompt)
        # 加锁保护缓存写入（避免并发写入损坏）
        async with KPMatcher._async_lock:
            save_cache(cache_key, result, self.cache_dir, prompt=prompt)

    # LLM调用上限：只对前N个候选做LLM投票
    LLM_CANDIDATE_LIMIT = 3
    # 向量相似度阈值：低于此值不做LLM投票
    SIMILARITY_THRESHOLD = 0.5

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
        3. 早停机制：匹配成功后立即停止
        4. LLM调用上限：只对前N个候选做LLM投票
        5. 相似度阈值：低相似度候选直接跳过

        Args:
            textbook_kp: 教材知识点
            kg_concepts: 图谱知识点列表
            top_k: 返回前 K 个匹配结果

        Returns:
            匹配结果列表
        """
        results = []
        textbook_kp_name = textbook_kp.get('label', '')
        textbook_kp_stage = textbook_kp.get('stage', '')
        textbook_kp_grade = textbook_kp.get('grade', '')
        textbook_kp_desc = f"学段: {textbook_kp_stage}, 年级: {textbook_kp_grade}"

        # 获取标准化名称（用于记录）
        normalized_name = self.get_best_match(textbook_kp_name, textbook_kp_stage, textbook_kp_grade)

        # 1. 粗筛：只对 top-N 候选进行 LLM 匹配（使用标准化名称）
        candidates = self._retrieve_candidates(
            textbook_kp_name, kg_concepts, self.candidate_top_n,
            stage=textbook_kp_stage, grade=textbook_kp_grade
        )

        logger.debug(f"粗筛结果: {textbook_kp_name} -> {len(candidates)} 个候选")

        # 2. 对每个候选进行 LLM 投票（有上限）
        llm_calls = 0  # 记录LLM调用次数
        best_unmatched = None  # 记录最佳未匹配候选（用于后续分析）
        for i, concept in enumerate(candidates):
            kg_kp_name = concept.get('label', '')
            kg_kp_desc = concept.get('description', '')
            similarity = concept.get('score', 1.0)  # 向量相似度

            # 检查相似度阈值（低相似度直接跳过）
            if similarity < self.SIMILARITY_THRESHOLD:
                logger.debug(f"跳过低相似度候选: {kg_kp_name} (sim={similarity:.2f})")
                continue

            # 检查LLM调用上限
            if llm_calls >= self.LLM_CANDIDATE_LIMIT:
                logger.debug(f"LLM调用上限已达 ({self.LLM_CANDIDATE_LIMIT})，停止遍历")
                # 记录最佳未匹配候选
                if best_unmatched is None and i < 5:
                    best_unmatched = {
                        'kg_uri': concept['uri'],
                        'kg_name': kg_kp_name,
                        'similarity': similarity,
                        'reason': 'LLM调用上限，待人工审核'
                    }
                break

            # 格式化 Prompt
            prompt = format_kp_match_prompt(
                textbook_kp_name=textbook_kp_name,
                textbook_kp_description=textbook_kp_desc,
                kg_kp_name=kg_kp_name,
                kg_kp_description=kg_kp_desc or "无描述"
            )

            try:
                # 检查缓存（并发安全）
                cached_result = await self._get_cached_result(prompt)
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
                            'from_cache': True,
                            'similarity': similarity
                        })
                        # 早停：匹配成功后立即停止
                        break
                    continue

                # 执行投票（计数）
                llm_calls += 1
                vote_result = await vote_with_retry(self.voter, prompt)

                # 保存到缓存（并发安全）
                await self._save_cached_result(prompt, vote_result)

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
                            'reason': result.get('primary_reason', ''),
                            'similarity': similarity
                        })
                        # 早停：匹配成功后立即停止
                        break
                    else:
                        # 记录最佳未匹配候选
                        if best_unmatched is None or similarity > best_unmatched['similarity']:
                            best_unmatched = {
                                'kg_uri': concept['uri'],
                                'kg_name': kg_kp_name,
                                'similarity': similarity,
                                'confidence': confidence,
                                'reason': '投票不通过'
                            }

            except Exception as e:
                self.stats['errors'] += 1
                logger.warning(f"LLM调用失败: {textbook_kp_name} -> {kg_kp_name}, 错误: {e}")
                continue  # 继续下一个候选

        # 按置信度排序，返回 top_k
        results.sort(key=lambda x: x.get('confidence', 0), reverse=True)

        # 如果没有匹配成功，返回最佳未匹配候选信息
        if not results and best_unmatched:
            return [{'best_candidate': best_unmatched}]

        return results[:top_k]

    async def _match_single_concurrent(
        self,
        kp: Dict,
        kg_concepts: List[Dict],
        use_llm: bool = True,
        index: int = 0,
        total: int = 0
    ) -> tuple:
        """
        并发安全地匹配单个知识点

        改进（采纳 DeepSeek 建议方案 C）：
        - 返回 (result, match_type) 元组，由主流程汇总统计
        - 每个任务完成后立即持久化（加锁保护）
        - 简化等待逻辑，依赖 _processing_uris 状态

        Args:
            kp: 单个教材知识点
            kg_concepts: 图谱知识点列表
            use_llm: 是否使用 LLM
            index: 当前索引（用于进度显示）
            total: 总数

        Returns:
            (result, match_type) 元组，match_type 为 "exact_match", "llm_match", "unmatched", "error"
        """
        kp_uri = kp.get('uri', '')
        kp_name = kp.get('label', '')
        kp_stage = kp.get('stage', '')
        kp_grade = kp.get('grade', '')
        checkpoint_id = f"kp_{kp_uri.split('#')[-1]}"

        # 加锁检查处理状态
        need_wait = False
        async with KPMatcher._async_lock:
            if kp_uri in KPMatcher._processing_uris:
                need_wait = True
            else:
                KPMatcher._processing_uris.add(kp_uri)

        if need_wait:
            # 等待其他协程完成
            max_wait = 30  # 最大等待30秒
            waited = 0
            while waited < max_wait:
                await asyncio.sleep(0.1)
                waited += 0.1
                async with KPMatcher._async_lock:
                    if kp_uri not in KPMatcher._processing_uris:
                        # 前面处理完成或失败，接手处理
                        KPMatcher._processing_uris.add(kp_uri)
                        break

            # 超时后检查状态
            async with KPMatcher._async_lock:
                if kp_uri in KPMatcher._processing_uris:
                    # 其他协程仍在处理，返回默认结果避免重复
                    logger.warning(f"等待超时，其他协程仍在处理: {kp_name}")
                    return {
                        'textbook_kp_uri': kp_uri,
                        'textbook_kp_name': kp_name,
                        'kg_uri': None,
                        'kg_name': None,
                        'confidence': 0.0,
                        'method': 'timeout',
                        'matched': False,
                        'reason': '等待超时，放弃处理避免重复'
                    }, 'unmatched'
                # 接手处理
                KPMatcher._processing_uris.add(kp_uri)

        try:
            # 进度显示
            if index % 50 == 0 or index == 1:
                logger.info(f"[并发] 进度: {index}/{total} - {kp_name}")

            # 获取标准化名称（用于记录）
            normalized_name = self.get_best_match(kp_name, kp_stage, kp_grade)

            # 1. 先尝试精确匹配（使用标准化名称）
            match = self.exact_match(kp_name, kg_concepts, stage=kp_stage, grade=kp_grade)

            if match:
                result = {
                    'textbook_kp_uri': kp_uri,
                    'textbook_kp_name': kp_name,
                    'normalized_name': normalized_name if normalized_name != kp_name else None,
                    'kg_uri': match['kg_uri'],
                    'kg_name': match['kg_name'],
                    'confidence': match['confidence'],
                    'method': 'exact_match',
                    'matched': True
                }
                # 立即持久化（加锁）
                async with KPMatcher._async_lock:
                    self.task_state.complete_checkpoint(checkpoint_id, result)
                    self.task_state._save_state()
                return result, 'exact_match'

            elif use_llm:
                # 2. LLM 匹配
                llm_results = await self.llm_match_with_cache(kp, kg_concepts, top_k=1)

                if llm_results:
                    first_result = llm_results[0]
                    if 'best_candidate' in first_result:
                        best = first_result['best_candidate']
                        result = {
                            'textbook_kp_uri': kp_uri,
                            'textbook_kp_name': kp_name,
                            'normalized_name': normalized_name if normalized_name != kp_name else None,
                            'kg_uri': best['kg_uri'],
                            'kg_name': best['kg_name'],
                            'confidence': best.get('confidence', 0.0),
                            'similarity': best.get('similarity', 0.0),
                            'method': 'candidate_review',
                            'matched': False,
                            'reason': f"最佳候选待审核: {best['reason']}"
                        }
                        # 立即持久化（加锁）
                        async with KPMatcher._async_lock:
                            self.task_state.complete_checkpoint(checkpoint_id, result)
                            self.task_state._save_state()
                        return result, 'unmatched'
                    else:
                        first_result['matched'] = True
                        first_result['normalized_name'] = normalized_name if normalized_name != kp_name else None
                        # 立即持久化（加锁）
                        async with KPMatcher._async_lock:
                            self.task_state.complete_checkpoint(checkpoint_id, first_result)
                            self.task_state._save_state()
                        return first_result, 'llm_match'
                else:
                    result = {
                        'textbook_kp_uri': kp_uri,
                        'textbook_kp_name': kp_name,
                        'normalized_name': normalized_name if normalized_name != kp_name else None,
                        'kg_uri': None,
                        'kg_name': None,
                        'confidence': 0.0,
                        'method': 'none',
                        'matched': False,
                        'reason': 'LLM匹配失败，无候选通过'
                    }
                    # 立即持久化（加锁）
                    async with KPMatcher._async_lock:
                        self.task_state.complete_checkpoint(checkpoint_id, result)
                        self.task_state._save_state()
                    return result, 'unmatched'
            else:
                result = {
                    'textbook_kp_uri': kp_uri,
                    'textbook_kp_name': kp_name,
                    'normalized_name': normalized_name if normalized_name != kp_name else None,
                    'kg_uri': None,
                    'kg_name': None,
                    'confidence': 0.0,
                    'method': 'none',
                    'matched': False,
                    'reason': '精确匹配失败，LLM未启用'
                }
                # 立即持久化（加锁）
                async with KPMatcher._async_lock:
                    self.task_state.complete_checkpoint(checkpoint_id, result)
                    self.task_state._save_state()
                return result, 'unmatched'

        except Exception as e:
            logger.error(f"匹配失败: {kp_name}, 错误: {e}")
            result = {
                'textbook_kp_uri': kp_uri,
                'textbook_kp_name': kp_name,
                'kg_uri': None,
                'kg_name': None,
                'confidence': 0.0,
                'method': 'error',
                'matched': False,
                'reason': f'匹配异常: {e}'
            }
            # 立即持久化（加锁）
            async with KPMatcher._async_lock:
                self.task_state.complete_checkpoint(checkpoint_id, result)
                self.task_state._save_state()
            return result, 'error'
        finally:
            # 移除处理中标记
            async with KPMatcher._async_lock:
                KPMatcher._processing_uris.discard(kp_uri)

    async def match_all(
        self,
        textbook_kps: List[Dict],
        kg_concepts: List[Dict],
        use_llm: bool = True,
        resume: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        checkpoint_interval: int = 10,
        max_concurrent: int = 1
    ) -> List[Dict]:
        """
        批量匹配所有知识点

        改进：
        1. 输出所有知识点，增加 matched 字段
        2. 使用 processed_count 作为进度
        3. 支持并发处理（max_concurrent > 1）

        Args:
            textbook_kps: 教材知识点列表
            kg_concepts: 图谱知识点列表
            use_llm: 是否使用 LLM 匹配（默认 True）
            resume: 是否支持断点续传（默认 True）
            progress_callback: 进度回调函数
            checkpoint_interval: 每 N 个知识点保存一次进度
            max_concurrent: 最大并发数（默认 1，串行处理）

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

        # 并发处理分支（改进：方案 C - 返回值汇总统计）
        if max_concurrent > 1:
            logger.info(f"并发模式: {max_concurrent} 个并发任务")

            semaphore = asyncio.Semaphore(max_concurrent)

            async def _process_with_semaphore(kp: Dict, idx: int):
                async with semaphore:
                    return await self._match_single_concurrent(
                        kp, kg_concepts, use_llm, idx, len(pending_kps)
                    )

            # 创建并发任务
            tasks = [_process_with_semaphore(kp, i) for i, kp in enumerate(pending_kps, 1)]

            # 使用 as_completed 实时显示进度
            for coro in asyncio.as_completed(tasks):
                result, match_type = await coro
                if result:
                    results.append(result)
                    # 汇总统计（主线程安全）
                    if match_type == 'checkpoint_hit':
                        self.stats['cache_hits'] += 1
                    elif match_type in self.stats:
                        self.stats[match_type] += 1
                    elif match_type == 'error':
                        self.stats['errors'] += 1

            # 进度已由各协程立即持久化，此处无需批量保存

        else:
            # 串行处理（原有逻辑）
            # 使用进程锁保护
            with self.process_lock:
                processed_count = 0

                for kp in pending_kps:
                    kp_uri = kp.get('uri', '')
                    kp_name = kp.get('label', '')
                    kp_stage = kp.get('stage', '')
                    kp_grade = kp.get('grade', '')
                    processed_count += 1

                    # 显示进度（含已恢复的结果）
                    completed_total = len(results) + 1  # 包含正在处理的这一个
                    if processed_count % checkpoint_interval == 0 or processed_count == 1:
                        logger.info(f"进度: {completed_total}/{total} ({completed_total / total * 100:.1f}%) - {kp_name}")

                    # 进度回调（使用实际已完成数量）
                    if progress_callback:
                        progress_callback(completed_total, total, kp_name)

                    # 获取标准化名称（用于记录）
                    normalized_name = self.get_best_match(kp_name, kp_stage, kp_grade)

                    # 1. 先尝试精确匹配（使用标准化名称）
                    match = self.exact_match(kp_name, kg_concepts, stage=kp_stage, grade=kp_grade)

                    if match:
                        result = {
                            'textbook_kp_uri': kp_uri,
                            'textbook_kp_name': kp_name,
                            'normalized_name': normalized_name if normalized_name != kp_name else None,
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
                            first_result = llm_results[0]
                            # 检查是否有 best_candidate（未匹配但有候选信息）
                            if 'best_candidate' in first_result:
                                # 未匹配，但有最佳候选供人工审核
                                best = first_result['best_candidate']
                                result = {
                                    'textbook_kp_uri': kp_uri,
                                    'textbook_kp_name': kp_name,
                                    'kg_uri': best['kg_uri'],
                                    'kg_name': best['kg_name'],
                                    'confidence': best.get('confidence', 0.0),
                                    'similarity': best.get('similarity', 0.0),
                                    'method': 'candidate_review',
                                    'matched': False,
                                    'reason': f"最佳候选待审核: {best['reason']}"
                                }
                                results.append(result)
                                self.stats['unmatched'] += 1
                            else:
                                # 匹配成功
                                first_result['matched'] = True
                                results.append(first_result)
                                self.stats['llm_match'] += 1

                            checkpoint_id = f"kp_{kp_uri.split('#')[-1]}"
                            self.task_state.complete_checkpoint(checkpoint_id, result if 'best_candidate' in first_result else first_result)
                        else:
                            # 完全未匹配（无候选）
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