"""
课标知识点提取模块

从课标 PDF 构建 Neo4j 知识图谱的完整流程。

Quick Start:
    from edukg.core.curriculum import build_knowledge_graph

    result = build_knowledge_graph(
        ocr_result_path="ocr_result.json",
        output_dir="output/",
    )

模块结构:
    pdf_ocr.py          - PDF OCR 服务（百度 OCR，收费）
    kp_extraction.py    - 知识点提取（LLM，免费）
    class_extractor.py  - Class 类型推断（LLM）
    concept_extractor.py - Concept 生成
    statement_extractor.py - Statement 定义生成（LLM）
    relation_extractor.py - 关系提取（LLM + 规则）
    kg_builder.py       - 基础设施（URI 生成）
    kg_main.py          - 主流程
    kp_comparison.py    - 知识点对比
    ttl_generator.py    - TTL 生成
    config.py           - 配置
"""

from .config import settings, Settings
from .kg_builder import KGBuilder, URIGenerator, KGConfig
from .pdf_ocr import BaiduOCRService, OCRResult
from .kp_extraction import LLMExtractor, CurriculumKnowledgePoints
from .class_extractor import ClassExtractor, ClassExtractionResult
from .concept_extractor import ConceptExtractor
from .statement_extractor import StatementExtractor
from .relation_extractor import RelationExtractor
from .kp_comparison import ConceptComparator, ComparisonReport
from .ttl_generator import TTLGenerator, TTLConfig

# 主流程函数
from .kg_main import build_knowledge_graph

__all__ = [
    # 配置
    "settings",
    "Settings",
    # 基础设施
    "KGBuilder",
    "URIGenerator",
    "KGConfig",
    # OCR
    "BaiduOCRService",
    "OCRResult",
    # 知识点提取
    "LLMExtractor",
    "CurriculumKnowledgePoints",
    # Class 提取
    "ClassExtractor",
    "ClassExtractionResult",
    # Concept 提取
    "ConceptExtractor",
    # Statement 提取
    "StatementExtractor",
    # 关系提取
    "RelationExtractor",
    # 对比
    "ConceptComparator",
    "ComparisonReport",
    # TTL
    "TTLGenerator",
    "TTLConfig",
    # 主流程
    "build_knowledge_graph",
]