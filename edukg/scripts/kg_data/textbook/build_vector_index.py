#!/usr/bin/env python3
"""
向量索引构建脚本

构建 EduKG 知识点向量索引并保存到文件。

用法:
    python build_vector_index.py           # 构建索引
    python build_vector_index.py --status  # 查看索引状态
    python build_vector_index.py --force   # 强制重建索引
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# 设置路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AI_SERVICE_DIR = PROJECT_ROOT / "ai-edu-ai-service"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(AI_SERVICE_DIR))

import os
os.chdir(str(AI_SERVICE_DIR))  # 加载 .env

from dotenv import load_dotenv
load_dotenv()

from edukg.core.neo4j.client import Neo4jClient
from edukg.core.textbook.vector_index_manager import VectorIndexManager, DEFAULT_OUTPUT_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class VectorIndexBuilder:
    """向量索引构建器"""

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        self.manager = VectorIndexManager(model_name)
        self.neo4j_client = None

    def connect_neo4j(self):
        """连接 Neo4j"""
        # Neo4jClient 在初始化时自动连接
        if self.neo4j_client is None:
            self.neo4j_client = Neo4jClient()

    def close(self):
        """关闭连接"""
        if self.neo4j_client:
            self.neo4j_client.close()

    def load_kg_concepts(self) -> list:
        """从 Neo4j 加载 EduKG Concept

        Returns:
            知识点列表 [{"uri": ..., "label": ..., "description": ...}]
        """
        if not self.neo4j_client:
            self.connect_neo4j()

        query = """
        MATCH (c:Concept)
        OPTIONAL MATCH (s:Statement)-[:RELATED_TO]->(c)
        WITH c, collect(s.content) AS descriptions
        RETURN c.uri AS uri, c.label AS label, descriptions[0] AS description
        ORDER BY c.uri
        """

        concepts = []
        with self.neo4j_client.session() as session:
            result = session.run(query)
            for record in result:
                concepts.append({
                    "uri": record.get("uri", ""),
                    "label": record.get("label", ""),
                    "description": record.get("description", "")
                })

        logger.info(f"加载 EduKG Concept: {len(concepts)} 个")
        return concepts

    def build_index(self, output_dir: Path = DEFAULT_OUTPUT_DIR, force: bool = False):
        """构建向量索引

        Args:
            output_dir: 输出目录
            force: 强制重建
        """
        # 检查是否需要重建
        meta_path = output_dir / "index_meta.json"
        if meta_path.exists() and not force:
            logger.info(f"索引已存在: {output_dir}")
            with open(meta_path, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
            logger.info(f"  模型: {existing_meta.get('model_name')}")
            logger.info(f"  知识点数: {existing_meta.get('concept_count')}")
            logger.info(f"  创建时间: {existing_meta.get('created_at')}")
            logger.info("使用 --force 强制重建")
            return False

        # 加载知识点
        concepts = self.load_kg_concepts()
        if not concepts:
            logger.warning("Neo4j 中无知识点数据")
            return False

        # 进度回调
        def progress_callback(processed, total, message):
            if processed > 0:
                percent = processed / total * 100
                logger.info(f"[{percent:.1f}%] {message}")

        # 构建索引
        logger.info("开始构建向量索引...")
        self.manager.build_index(concepts, progress_callback)

        # 保存索引
        meta = self.manager.save_index(output_dir)

        logger.info(f"索引构建完成!")
        logger.info(f"  输出目录: {output_dir}")
        logger.info(f"  向量维度: {meta['vector_dim']}")
        logger.info(f"  知识点数: {meta['concept_count']}")
        logger.info(f"  创建时间: {meta['created_at']}")

        return True

    def show_status(self, output_dir: Path = DEFAULT_OUTPUT_DIR):
        """显示索引状态（只读元数据，不加载向量）"""
        meta_path = output_dir / "index_meta.json"

        if not meta_path.exists():
            logger.info(f"索引不存在: {output_dir}")
            logger.info("运行 python build_vector_index.py 构建索引")
            return

        # 只读取元数据，不加载向量矩阵
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

            print("\n向量索引状态:")
            print(f"  模型: {meta.get('model_name')}")
            print(f"  向量维度: {meta.get('vector_dim')}")
            print(f"  知识点数: {meta.get('concept_count')}")
            print(f"  创建时间: {meta.get('created_at')}")
            print(f"  数据校验和: {meta.get('neo4j_checksum')}")

            # 检查有效性（需要从 Neo4j 加载 concepts 计算 checksum）
            concepts = self.load_kg_concepts()
            from edukg.core.textbook.vector_index_manager import VectorIndexManager
            manager = VectorIndexManager()
            current_checksum = manager.get_checksum(concepts)
            stored_checksum = meta.get("neo4j_checksum", "")

            if current_checksum == stored_checksum:
                print(f"  状态: ✓ 有效（checksum 匹配）")
            else:
                print(f"  状态: ⚠ 过期（checksum 不匹配，建议重建）")

        except Exception as e:
            logger.error(f"读取元数据失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="EduKG 向量索引构建脚本")
    parser.add_argument("--status", action="store_true", help="显示索引状态")
    parser.add_argument("--force", action="store_true", help="强制重建索引")
    parser.add_argument("--model", default="BAAI/bge-small-zh-v1.5", help="Embedding 模型名称")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")

    args = parser.parse_args()

    builder = VectorIndexBuilder(args.model)

    try:
        if args.status:
            builder.show_status(Path(args.output))
        else:
            builder.build_index(Path(args.output), args.force)
    finally:
        builder.close()


if __name__ == "__main__":
    main()