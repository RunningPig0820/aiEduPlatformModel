# 13.2.1 StateDB 类（MySQL 版）
> summary: StateDB 类封装章节状态、子批次状态、LLM缓存、进度查询、成本追踪的 MySQL 操作，支撑断点续传。
> 权威度: 0.7
> 模块: knowledge-graph
> COS路径: rag-slices/knowledge-graph/OpenSpec/design-python-2026-04-10-knowledge-graph-data-research-状态管理-mysql-2.md
> 类别：数据存储

> 检索摘要：StateDB 类封装章节状态、子批次状态、LLM缓存、进度查询、成本追踪的 MySQL 操作，支撑断点续传。

# scripts/state_db.py
from db_connection import db
from typing import Optional, List, Dict, Any
import json

class StateDB:
    """MySQL 状态管理类"""

    def __init__(self):
        self.db = db

    # ========== 章节状态 ==========

    def get_chapter_status(self, chapter_id: str) -> Optional[str]:
        """获取章节状态"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM chapter_state
                    WHERE chapter_id = %s
                """, (chapter_id,))
                result = cursor.fetchone()
                return result['status'] if result else None

    def mark_chapter_processing(self, chapter_id: str):
        """标记章节处理中"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'processing', started_at = NOW()
                    WHERE chapter_id = %s
                """, (chapter_id,))
            conn.commit()

    def mark_chapter_completed(self, chapter_id: str):
        """标记章节完成"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'completed', completed_at = NOW()
                    WHERE chapter_id = %s
                """, (chapter_id,))
            conn.commit()

    def mark_chapter_failed(self, chapter_id: str, error: str = ""):
        """标记章节失败"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'failed', error_message = %s, completed_at = NOW()
                    WHERE chapter_id = %s
                """, (error, chapter_id))
            conn.commit()

    def skip_chapter(self, chapter_id: str, reason: str = ""):
        """跳过章节"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE chapter_state
                    SET status = 'skipped', error_message = %s, completed_at = NOW()
                    WHERE chapter_id = %s
                """, (f"手动跳过: {reason}", chapter_id))
            conn.commit()

    # ========== 子批次状态 ==========

    def is_subbatch_completed(self, batch_id: str) -> bool:
        """检查子批次是否完成"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT status FROM subbatch_state
                    WHERE batch_id = %s
                """, (batch_id,))
                result = cursor.fetchone()
                return result and result['status'] == 'completed'

    def mark_subbatch_completed(self, batch_id: str, cache_key: str, result_file: str):
        """标记子批次完成"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE subbatch_state
                    SET status = 'completed',
                        cache_key = %s,
                        result_file = %s,
                        completed_at = NOW()
                    WHERE batch_id = %s
                """, (cache_key, result_file, batch_id))
            conn.commit()

    def mark_subbatch_failed(self, batch_id: str, error: str):
        """标记子批次失败"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE subbatch_state
                    SET status = 'failed',
                        error_message = %s,
                        retry_count = retry_count + 1
                    WHERE batch_id = %s
                """, (error, batch_id))
            conn.commit()

    # ========== LLM 缓存 ==========

    def get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """获取缓存的 LLM 响应"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT response, result_file FROM llm_cache
                    WHERE cache_key = %s
                """, (cache_key,))
                result = cursor.fetchone()
                if result:
                    return {
                        'response': result['response'],
                        'result_file': result['result_file']
                    }
                return None

    def save_cache(self, cache_key: str, provider: str, model: str,
                   batch_uris: List[str], response: Dict,
                   tokens: int = 0, cost: int = 0, result_file: str = ""):
        """保存 LLM 缓存"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO llm_cache
                    (cache_key, provider, model, batch_uris, response, tokens_used, cost_cents, result_file)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    response = VALUES(response),
                    tokens_used = VALUES(tokens_used),
                    cost_cents = VALUES(cost_cents)
                """, (cache_key, provider, model,
                      json.dumps(batch_uris), json.dumps(response),
                      tokens, cost, result_file))
            conn.commit()

    # ========== 进度查询 ==========

    def get_progress(self, subject: str, version: str) -> Dict:
        """获取处理进度"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM progress_view
                    WHERE subject = %s AND version = %s
                """, (subject, version))
                return cursor.fetchone() or {}

    def get_failed_chapters(self, subject: str, version: str) -> List[Dict]:
        """获取失败章节"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT chapter_id, chapter_name, error_message
                    FROM chapter_state
                    WHERE subject = %s AND version = %s AND status = 'failed'
                """, (subject, version))
                return cursor.fetchall()

    # ========== 成本追踪 ==========

    def track_cost(self, subject: str, version: str, provider: str,
                   model: str, tokens: int, cost: int):
        """记录成本"""
        with self.db.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO cost_tracking
                    (subject, version, provider, model, total_tokens, total_cost_cents, call_count)
                    VALUES (%s, %s, %s, %s, %s, %s, 1)
                    ON DUPLICATE KEY UPDATE
                    total_tokens = total_tokens + VALUES(total_tokens),
                    total_cost_cents = total_cost_cents + VALUES(total_cost_cents),
                    call_count = call_count + 1,
                    updated_at = NOW()
                """, (subject, version, provider, model, tokens, cost))
            conn.commit()

> 证据：详见 `2.OpenSpec design 决策/design-python-2026-04-10-knowledge-graph-data-research.md`（§13.2 状态管理（MySQL））
