"""
配置管理 - 使用 Pydantic Settings 从环境变量加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置 - 从环境变量加载，支持 .env 文件"""

    # ============ LLM API Keys ============
    # 智谱 AI (GLM 系列)
    ZHIPU_API_KEY: str = ""

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""

    # 阿里云百炼 (通义千问)
    BAILIAN_API_KEY: str = ""

    # 阿里云 DashScope API Key (百炼使用)
    DASHSCOPE_API_KEY: str = ""

    # ============ 百度 OCR ============
    # 百度 OCR API Key (拍照识别题目)
    BAIDU_OCR_API_KEY: str = ""
    BAIDU_OCR_SECRET_KEY: str = ""

    # ============ 豆包(火山方舟) ============
    # 火山方舟 API Key (看图答疑用 doubao-seed-2-0-mini)
    DOUBAO_API_KEY: str = ""

    # ============ 服务配置 ============
    # Java 后端调用 AI 服务的内部 Token
    INTERNAL_TOKEN: str = ""

    # 服务端口
    PORT: int = 8000

    # 调试模式
    DEBUG: bool = False

    # ============ 默认模型配置 ============
    # 默认使用的 LLM Provider
    DEFAULT_PROVIDER: str = "zhipu"

    # 默认模型
    DEFAULT_MODEL: str = "glm-4-flash"

    # ============ AI 答疑 (Tutoring) 模型配置 ============
    # 看图答疑需视觉能力(design 决策 14) → 豆包 doubao-seed-2-0-mini
    # 2026-08: 全关思考模式(见 tutoring-streaming-experience.md)——mini 关思考看图实测 1.2s 出答案,
    # 开思考要 50~145s(思考模式 = 模型写草稿,卡顿根源)。decide/generate 均关思考。
    # decide 决策模型(判断密集)
    TUTORING_DECIDE_PROVIDER: str = "doubao"
    TUTORING_DECIDE_MODEL: str = "doubao-seed-2-0-mini-260428"

    # generate 生成模型(内容生成)
    TUTORING_GENERATE_PROVIDER: str = "doubao"
    TUTORING_GENERATE_MODEL: str = "doubao-seed-2-0-mini-260428"

    # 温度: decide 偏低(判断要稳), generate 偏高(内容要有层次)
    TUTORING_DECIDE_TEMPERATURE: float = 0.3
    TUTORING_GENERATE_TEMPERATURE: float = 0.7

    # ============ 日志配置 ============
    LOG_LEVEL: str = "INFO"

    # ============ Neo4j 知识图谱配置 ============
    # Neo4j 连接 URI (bolt 协议)
    NEO4J_URI: str = "bolt://localhost:7687"

    # Neo4j HTTP 端口 (浏览器访问)
    NEO4J_HTTP_URI: str = "http://localhost:7474"

    # Neo4j 用户名
    NEO4J_USER: str = "neo4j"

    # Neo4j 密码
    NEO4J_PASSWORD: str = ""

    # ============ Redis 配置 (可选) ============
    REDIS_URL: str = ""

    # ============ COS 向量桶 (题型聚集向量服务) ============
    # 腾讯云 COS 向量桶(Vertex Bucket)——Java 无 SDK, 向量操作走 Python 桥。
    # 复用 DASHSCOPE_API_KEY 做 embedding, 不新增密钥。
    COS_VECTORS_SECRET_ID: str = ""
    COS_VECTORS_SECRET_KEY: str = ""
    COS_VECTORS_REGION: str = "ap-guangzhou"
    COS_VECTORS_BUCKET: str = ""                # "xxx-125xxxxxxx" 题型聚集(topic)
    COS_VECTORS_RAG_BUCKET: str = ""            # RAG 独立向量桶 "rag-1318177119"(topic 不混)

    # 逻辑类型 → 物理索引 路由表(多索引)。vector_type 必填, 每次 put/query 由 Java 显式传入。
    # topic(题型名向量) 走 COS_VECTORS_BUCKET; rag/rag-full/rag-slice(AI答疑 RAG) 走 COS_VECTORS_RAG_BUCKET。
    # 桶按 vector_type 路由(vector_store._resolve_bucket_index), 新增桶仅需加配置。
    # rag-full/rag-slice = 双池检索(2026-08-26): rag-full 全量池(整篇, 管整体问题), rag-slice 切片池(细节块)。
    # rag(旧 rag-index) 被双池取代, 保留映射仅为向后兼容, 不建新数据。
    COS_VECTORS_INDEXES: dict = {
        "topic": "topic-index",
        # "question": "question-index",         # 相似题, 预留不建
        "rag": "rag-index",                     # 旧单池(AI答疑/知识图谱/组织中心), 双池上线后废弃
        "rag-full": "rag-full",                 # 双池-全量池: 语雀5+完善文档8+代码10 整篇(23 块)
        "rag-slice": "rag-slice",               # 双池-切片池: 切片数据/ 294 块(细节)
    }

    # RAG 语料根目录(前端按 file_path 访问源文件; 相对项目根)
    # 前端拼 {/api/rag/source}/{file_path} 即可拿到源文件内容
    RAG_CORPUS_DIR: str = "docs/rag/ai-tutoring"

    # ============ COS 普通桶 (RAG 源文件, "查看原文"用, 阶段 2 定稿) ============
    # 切片数据 + 源语料上传 ai-edu-1318177119; file_path 记录 COS key。
    # /api/rag/source 从该桶读文件(U4, 替代本地 StaticFiles)。凭据复用 COS_VECTORS_*。
    COS_OBJ_BUCKET: str = "ai-edu-1318177119"
    COS_OBJ_REGION: str = "ap-guangzhou"

    # ============ RAG 白盒链路超时(A3/C 韧性) ============
    # 分层超时: 召回单路 2s(向量 COS 网络路), 生成 8s(doubao 流式)。超时写死降级话术 0 token。
    RAG_RECALL_TIMEOUT: float = 2.0
    RAG_GEN_TIMEOUT: float = 8.0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略 .env 中的额外字段


# 单例
settings = Settings()