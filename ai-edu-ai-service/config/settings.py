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
    # decide 决策模型(判断密集,选便宜快;测试阶段用 deepseek-v4-flash 走流程)
    TUTORING_DECIDE_PROVIDER: str = "deepseek"
    TUTORING_DECIDE_MODEL: str = "deepseek-v4-flash"

    # generate 生成模型(内容生成)
    TUTORING_GENERATE_PROVIDER: str = "deepseek"
    TUTORING_GENERATE_MODEL: str = "deepseek-v4-flash"

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略 .env 中的额外字段


# 单例
settings = Settings()