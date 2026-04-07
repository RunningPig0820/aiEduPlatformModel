"""
EduKG 配置模块

从 ai-edu-ai-service/.env 加载环境变量
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# 找到 .env 文件路径 (在 ai-edu-ai-service/ 目录下)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / "ai-edu-ai-service" / ".env"

# 加载环境变量
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    """配置类"""

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH) if ENV_PATH.exists() else None,
        extra="ignore",
    )

    # Neo4j 配置
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = 50
    NEO4J_CONNECTION_TIMEOUT: int = 30

    # 百度 OCR 配置
    BAIDU_OCR_API_KEY: str = ""
    BAIDU_OCR_SECRET_KEY: str = ""

    # 智谱 AI 配置
    ZHIPU_API_KEY: str = ""

    # DeepSeek 配置
    DEEPSEEK_API_KEY: str = ""

    # 百炼配置
    BAILIAN_API_KEY: str = ""

    # 输出目录
    OUTPUT_DIR: Path = Path(__file__).parent.parent / "data" / "output"

    def get_output_dir(self) -> Path:
        """获取输出目录，如果不存在则创建"""
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        return self.OUTPUT_DIR


# 全局配置实例
settings = Settings()