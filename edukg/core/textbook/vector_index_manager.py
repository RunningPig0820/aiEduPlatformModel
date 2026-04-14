"""
向量索引管理模块

管理 EduKG 知识点向量索引的构建、存储、加载和验证。
"""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from edukg.core.textbook.config import VECTOR_INDEX_DIR

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_MODEL_NAME = "BAAI/bge-small-zh-v1.5"
DEFAULT_OUTPUT_DIR = VECTOR_INDEX_DIR  # 使用 config.py 中的配置
VECTOR_DIM = 512  # bge-small-zh-v1.5 的向量维度


class VectorIndexManager:
    """向量索引管理器

    负责构建、保存、加载和验证向量索引。

    索引文件:
    - kg_vectors.npy: 向量矩阵 (N, 512)
    - kg_texts.json: 知识点文本列表
    - kg_concepts.json: 知识点元数据
    - index_meta.json: 索引元数据（含 checksum）
    """

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        """初始化向量索引管理器

        Args:
            model_name: Embedding 模型名称
        """
        self.model_name = model_name
        self.vectors: Optional[np.ndarray] = None
        self.texts: List[str] = []
        self.concepts: List[Dict] = []
        self.meta: Dict = {}

    def build_index(
        self,
        kg_concepts: List[Dict],
        progress_callback: Optional[callable] = None
    ) -> Tuple[np.ndarray, List[str], List[Dict]]:
        """构建向量索引

        Args:
            kg_concepts: 图谱知识点列表，每个包含 uri, label, description
            progress_callback: 进度回调函数 (processed, total, message)

        Returns:
            (vectors, texts, concepts)
        """
        from sentence_transformers import SentenceTransformer

        # 强制离线模式，避免联网检查更新
        import os
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"

        # 加载模型
        logger.info(f"加载 Embedding 模型: {self.model_name} (离线模式)")
        model = SentenceTransformer(self.model_name)

        # 提取知识点文本
        total = len(kg_concepts)
        self.texts = []
        self.concepts = []

        for i, concept in enumerate(kg_concepts):
            # 构建文本: label + description（如果有）
            text = concept.get("label", "")
            if concept.get("description"):
                text += f" {concept['description']}"
            self.texts.append(text)
            self.concepts.append({
                "uri": concept.get("uri"),
                "label": concept.get("label"),
                "description": concept.get("description", "")
            })

            # 进度回调（每 100 个）
            if progress_callback and (i + 1) % 100 == 0:
                progress_callback(i + 1, total, f"处理知识点: {concept.get('label')}")

        # 构建向量
        logger.info(f"构建向量索引: {total} 个知识点")
        if progress_callback:
            progress_callback(0, total, "开始构建向量...")

        self.vectors = model.encode(
            self.texts,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        if progress_callback:
            progress_callback(total, total, "向量构建完成")

        logger.info(f"向量矩阵 shape: {self.vectors.shape}")

        return self.vectors, self.texts, self.concepts

    def save_index(self, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Dict:
        """保存索引到文件

        Args:
            output_dir: 输出目录

        Returns:
            元数据字典
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.vectors is None:
            raise ValueError("索引未构建，请先调用 build_index()")

        # 保存向量
        vectors_path = output_dir / "kg_vectors.npy"
        np.save(vectors_path, self.vectors)
        logger.info(f"保存向量: {vectors_path}")

        # 保存文本
        texts_path = output_dir / "kg_texts.json"
        with open(texts_path, "w", encoding="utf-8") as f:
            json.dump(self.texts, f, ensure_ascii=False, indent=2)
        logger.info(f"保存文本: {texts_path}")

        # 保存知识点元数据
        concepts_path = output_dir / "kg_concepts.json"
        with open(concepts_path, "w", encoding="utf-8") as f:
            json.dump(self.concepts, f, ensure_ascii=False, indent=2)
        logger.info(f"保存知识点: {concepts_path}")

        # 构建元数据
        self.meta = {
            "model_name": self.model_name,
            "vector_dim": self.vectors.shape[1],
            "concept_count": len(self.concepts),
            "created_at": datetime.now().isoformat(),
            "neo4j_checksum": self._compute_checksum(self.concepts)
        }

        # 保存元数据
        meta_path = output_dir / "index_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)
        logger.info(f"保存元数据: {meta_path}")

        return self.meta

    def load_index(self, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Tuple[np.ndarray, List[str], List[Dict]]:
        """加载预构建索引

        Args:
            output_dir: 索引目录

        Returns:
            (vectors, texts, concepts)
        """
        output_dir = Path(output_dir)

        # 检查文件存在
        vectors_path = output_dir / "kg_vectors.npy"
        texts_path = output_dir / "kg_texts.json"
        concepts_path = output_dir / "kg_concepts.json"
        meta_path = output_dir / "index_meta.json"

        if not vectors_path.exists():
            raise FileNotFoundError(f"索引文件不存在: {vectors_path}")

        # 加载向量
        self.vectors = np.load(vectors_path)
        logger.info(f"加载向量: shape={self.vectors.shape}")

        # 加载文本
        with open(texts_path, "r", encoding="utf-8") as f:
            self.texts = json.load(f)
        logger.info(f"加载文本: {len(self.texts)} 条")

        # 加载知识点
        with open(concepts_path, "r", encoding="utf-8") as f:
            self.concepts = json.load(f)
        logger.info(f"加载知识点: {len(self.concepts)} 条")

        # 加载元数据
        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)
        self.model_name = self.meta.get("model_name", DEFAULT_MODEL_NAME)

        return self.vectors, self.texts, self.concepts

    def _compute_checksum(self, concepts: List[Dict]) -> str:
        """计算知识点数据的 checksum

        Args:
            concepts: 知识点列表

        Returns:
            MD5 checksum 字符串
        """
        # 使用 uri + label 生成 checksum
        data = "".join(
            f"{c.get('uri', '')}:{c.get('label', '')}"
            for c in sorted(concepts, key=lambda x: x.get("uri", ""))
        )
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    def get_checksum(self, concepts: List[Dict]) -> str:
        """计算给定知识点列表的 checksum

        Args:
            concepts: 知识点列表

        Returns:
            MD5 checksum
        """
        return self._compute_checksum(concepts)

    def is_index_valid(self, current_concepts: List[Dict]) -> bool:
        """检查索引是否有效（checksum 是否匹配）

        Args:
            current_concepts: 当前 Neo4j 中的知识点列表

        Returns:
            True 如果索引有效，False 如果过期
        """
        if not self.meta:
            return False

        current_checksum = self.get_checksum(current_concepts)
        stored_checksum = self.meta.get("neo4j_checksum", "")

        return current_checksum == stored_checksum

    def get_status(self) -> Dict:
        """获取索引状态信息

        Returns:
            状态字典
        """
        return {
            "model_name": self.model_name,
            "vector_dim": self.meta.get("vector_dim", VECTOR_DIM),
            "concept_count": len(self.concepts),
            "created_at": self.meta.get("created_at", ""),
            "checksum": self.meta.get("neo4j_checksum", ""),
            "is_loaded": self.vectors is not None
        }