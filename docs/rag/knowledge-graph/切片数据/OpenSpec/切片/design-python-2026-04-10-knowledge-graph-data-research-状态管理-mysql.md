# 13.2 状态管理（MySQL）
> summary: 状态管理用 MySQL 替代 SQLite：已有环境、并发性能好、运维工具丰富、有备份机制，承接处理状态/LLM缓存/成本表。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-状态管理-mysql.md
> 类别：数据存储

> 检索摘要：状态管理用 MySQL 替代 SQLite：已有环境、并发性能好、运维工具丰富、有备份机制，承接处理状态/LLM缓存/成本表。

使用 MySQL 替代 SQLite，原因：
● 已有 MySQL 环境，无需额外安装
● 支持更好的并发性能
● 支持更丰富的运维工具
● 数据更安全（有备份机制）

#### 13.2.0 数据库连接配置
> 检索摘要：MySQL 连接配置 database.yaml + pymysql 连接池，状态表设计含 processing_state/llm_cache/cost_tracking/两层状态表。

# config/database.yaml
mysql:
  host: "localhost"
  port: 3306
  database: "ai_edu_kg"
  user: "${MYSQL_USER}"
  password: "${MYSQL_PASSWORD}"
  charset: "utf8mb4"
  pool_size: 5

# scripts/db_connection.py
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
import yaml

class MySQLManager:
    def __init__(self, config_path: str = "config/database.yaml"):
        with open(config_path) as f:
            config = yaml.safe_load(f)['mysql']

        self.config = config
        self.pool = pymysql.ConnectionPool(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            charset=config['charset'],
            cursorclass=DictCursor,
            max_connections=config.get('pool_size', 5)
        )

    @contextmanager
    def get_connection(self):
        conn = self.pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self.pool.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

# 全局实例
db = MySQLManager()

状态表设计（MySQL 语法）：
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS ai_edu_kg
DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE ai_edu_kg;

-- 处理状态表
CREATE TABLE IF NOT EXISTS processing_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL COMMENT '学科',
    version VARCHAR(50) NOT NULL COMMENT '版本号',
    step VARCHAR(100) NOT NULL COMMENT '步骤名称',
    batch_id VARCHAR(200) COMMENT '批次ID（LLM调用）',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT 'pending/processing/completed/failed',
    result_file VARCHAR(500) COMMENT '结果文件路径',
    retry_count INT DEFAULT 0,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_step (subject, version, step, batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='处理状态表';

-- LLM 缓存表（付费模型结果）
CREATE TABLE IF NOT EXISTS llm_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    cache_key VARCHAR(64) UNIQUE NOT NULL COMMENT 'SHA256 哈希',
    provider VARCHAR(50) NOT NULL COMMENT '模型提供商',
    model VARCHAR(50) NOT NULL COMMENT '模型名称',
    batch_uris JSON NOT NULL COMMENT '知识点 URI 列表（JSON 数组）',
    response JSON NOT NULL COMMENT 'LLM 响应（JSON）',
    tokens_used INT DEFAULT 0,
    cost_cents INT DEFAULT 0 COMMENT '成本（分）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cache_key (cache_key),
    INDEX idx_provider_model (provider, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='LLM 缓存表';

-- 成本累积表
CREATE TABLE IF NOT EXISTS cost_tracking (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    total_tokens INT DEFAULT 0,
    total_cost_cents INT DEFAULT 0,
    call_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_provider (subject, version, provider, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='成本累积表';

-- ========== 两层状态表（章节 + 子批次）==========

-- 章节状态表（业务层）
CREATE TABLE IF NOT EXISTS chapter_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    chapter_id VARCHAR(200) NOT NULL COMMENT '如 math_chapter3_一元二次方程',
    chapter_name VARCHAR(200) NOT NULL,
    total_kps INT DEFAULT 0 COMMENT '该章节知识点总数',
    processed_kps INT DEFAULT 0 COMMENT '已处理知识点数',
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/processing/completed/skipped/failed',
    priority INT DEFAULT 0 COMMENT '优先级（0=普通，1=优先处理）',
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_chapter (subject, version, chapter_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='章节状态表';

-- 子批次状态表（技术层）
CREATE TABLE IF NOT EXISTS subbatch_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    chapter_id VARCHAR(200) NOT NULL,
    batch_id VARCHAR(200) NOT NULL COMMENT '如 math_chapter3_batch1',
    kp_uris JSON NOT NULL COMMENT '知识点 URI 列表（JSON 数组）',
    kp_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/processing/completed/failed',
    cache_key VARCHAR(64) COMMENT 'SHA256 缓存键',
    result_file VARCHAR(500) COMMENT '结果文件路径',
    retry_count INT DEFAULT 0,
    error_message TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_subject_version_batch (subject, version, batch_id),
    INDEX idx_chapter (chapter_id),
    INDEX idx_status (status),
    FOREIGN KEY (subject, version, chapter_id)
        REFERENCES chapter_state(subject, version, chapter_id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='子批次状态表';

-- 进度视图（便于查询）
CREATE OR REPLACE VIEW progress_view AS
SELECT
    subject,
    version,
    COUNT(*) as total_chapters,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_chapters,
    SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing_chapters,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_chapters,
    ROUND(100.0 * SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) / COUNT(*), 1) as progress_percent
FROM chapter_state
GROUP BY subject, version;

-- 失败批次表
CREATE TABLE IF NOT EXISTS failed_batches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    batch_id VARCHAR(200) NOT NULL,
    batch_uris JSON NOT NULL,
    error_type VARCHAR(50) NOT NULL COMMENT '错误类型分类',
    error_message TEXT,
    retry_count INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending/retrying/resolved/abandoned',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_retry_at DATETIME,
    INDEX idx_status (status),
    INDEX idx_error_type (error_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='失败批次表';

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.2 状态管理（MySQL））
