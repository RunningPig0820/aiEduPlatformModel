"""
教材数据处理配置

配置数据路径、输出路径、URI 版本等参数。
"""
from pathlib import Path

# ============ URI 配置 ============
# URI 版本号 (v3.1 避免与 EduKG v0.1/v0.2 冲突)
URI_VERSION = "3.1"
URI_PREFIX = f"http://edukg.org/knowledge/{URI_VERSION}"

# ============ 路径配置 ============
# 项目根目录 (config.py -> textbook -> core -> edukg -> PROJECT_ROOT)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# 数据目录
DATA_DIR = PROJECT_ROOT / "edukg" / "data" / "textbook" / "math" / "renjiao"

# 输出目录
OUTPUT_DIR = PROJECT_ROOT / "edukg" / "data" / "edukg" / "math" / "5_教材目录(Textbook)" / "output"

# ============ 学段配置 ============
STAGE_CONFIG = {
    "primary": {
        "name": "小学",
        "grade_dir": "primary",
        "grades": ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"],
        "semesters": ["上册", "下册"],
    },
    "middle": {
        "name": "初中",
        "grade_dir": "middle",
        "grades": ["七年级", "八年级", "九年级"],
        "semesters": ["上册", "下册"],
    },
    "high": {
        "name": "高中",
        "grade_dir": "high",
        "grades": ["必修第一册", "必修第二册", "必修第三册"],
        "semesters": [],  # 高中无学期
    }
}

# ============ 年级编码映射 ============
GRADE_ENCODING = {
    # 小学
    "一年级": "g1", "二年级": "g2", "三年级": "g3",
    "四年级": "g4", "五年级": "g5", "六年级": "g6",
    # 初中
    "七年级": "g7", "八年级": "g8", "九年级": "g9",
    # 高中
    "必修第一册": "bixiu1", "必修第二册": "bixiu2", "必修第三册": "bixiu3",
}

# ============ 学期编码映射 ============
SEMESTER_ENCODING = {
    "上册": "s",
    "下册": "x",
}

# ============ 出版社编码 ============
PUBLISHER_ENCODING = {
    "人民教育出版社": "renjiao",
    "人教版": "renjiao",
}

# ============ 输出文件名 ============
OUTPUT_FILES = {
    "textbooks": "textbooks.json",
    "chapters": "chapters.json",
    "sections": "sections.json",
    "textbook_kps": "textbook_kps.json",
    "contains_relations": "contains_relations.json",
    "in_unit_relations": "in_unit_relations.json",
    "matches_kg_relations": "matches_kg_relations.json",
    "import_summary": "import_summary.json",
}

# ============ 向量索引配置 ============
# 向量索引目录（与其他教材数据统一存放）
VECTOR_INDEX_DIR = OUTPUT_DIR / "vector_index"
VECTOR_INDEX_FILES = {
    "vectors": "kg_vectors.npy",
    "texts": "kg_texts.json",
    "concepts": "kg_concepts.json",
    "meta": "index_meta.json",
}