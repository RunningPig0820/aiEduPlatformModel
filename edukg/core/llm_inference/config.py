"""
LLM 推理配置

配置双模型投票和前置关系推断的相关参数。
"""

# ============ 模型配置 ============
# 主模型: 免费
PRIMARY_MODEL = "glm-4-flash"
# 副模型: DeepSeek-V3 (API标识符: deepseek-chat)
SECONDARY_MODEL = "deepseek-chat"

# ============ 投票阈值 ============
# 高置信度阈值: >= 此值标记为 PREREQUISITE
CONFIDENCE_THRESHOLD_HIGH = 0.8
# 低置信度阈值: >= 此值标记为 PREREQUISITE_CANDIDATE
CONFIDENCE_THRESHOLD_LOW = 0.6

# ============ 批量处理 ============
# 批处理大小
BATCH_SIZE = 10
# API 调用间隔（秒），避免速率限制
RATE_LIMIT_DELAY = 1.0
# 最大重试次数
MAX_RETRIES = 3
# 重试间隔（秒）
RETRY_DELAY = 2.0

# ============ LLM 调用配置 ============
# LLM Gateway 场景映射
SCENE_PREREQUISITE = "prerequisite_inference"
SCENE_KP_MATCH = "kp_match"

# ============ 输出路径 ============
# 输出目录
OUTPUT_DIR = "edukg/data/edukg/math/6_推理结果/output/"
# 输出文件名
TEACHES_BEFORE_FILE = "teaches_before.json"
DEFINITION_DEPS_FILE = "definition_deps.json"
LLM_PREREQ_FILE = "llm_prereq.json"
FINAL_PREREQ_FILE = "final_prereq.json"
VALIDATION_REPORT_FILE = "validation_report.json"

# ============ 日志配置 ============
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"