"""
课标知识点提取模块配置

从 ai-edu-ai-service/.env 加载环境变量
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 找到 .env 文件路径 (在 ai-edu-ai-service/ 目录下)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_PATH = PROJECT_ROOT / "ai-edu-ai-service" / ".env"

# 加载环境变量
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    # 尝试从当前目录加载
    load_dotenv()


class Settings:
    """配置类"""

    # 百度 OCR 配置
    BAIDU_OCR_API_KEY: str = os.getenv("BAIDU_OCR_API_KEY", "")
    BAIDU_OCR_SECRET_KEY: str = os.getenv("BAIDU_OCR_SECRET_KEY", "")

    # 智谱 AI 配置
    ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY", "")

    # Neo4j 配置
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "")

    # 输出目录
    OUTPUT_DIR: Path = Path(__file__).parent.parent.parent / "data" / "output"

    @classmethod
    def validate(cls) -> bool:
        """验证必要的环境变量是否配置"""
        missing = []

        if not cls.BAIDU_OCR_API_KEY:
            missing.append("BAIDU_OCR_API_KEY")
        if not cls.BAIDU_OCR_SECRET_KEY:
            missing.append("BAIDU_OCR_SECRET_KEY")
        if not cls.ZHIPU_API_KEY:
            missing.append("ZHIPU_API_KEY")
        if not cls.NEO4J_PASSWORD:
            missing.append("NEO4J_PASSWORD")

        if missing:
            print(f"警告: 以下环境变量未配置: {', '.join(missing)}")
            print(f"请在 {ENV_PATH} 中配置这些变量")
            return False
        return True


settings = Settings()