"""
任务 5.1: context.py 测试

历史截断(保留最近 ~12 条)、掌握度快照 top-N、模型路由(decide/generate 按配置取模型)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)


def _turns(n):
    return [{"role": "user", "content": f"第{i}条"} for i in range(n)]


class TestTruncateHistory:
    """历史截断"""

    def test_keeps_recent_n(self):
        from core.tutoring.context import truncate_history

        hist = _turns(30)
        result = truncate_history(hist, max_turns=12)
        assert len(result) == 12
        assert result[-1]["content"] == "第29条"  # 最新保留
        assert result[0]["content"] == "第18条"   # 最老的被截断

    def test_short_history_untouched(self):
        from core.tutoring.context import truncate_history

        hist = _turns(3)
        assert truncate_history(hist) == hist

    def test_empty_and_none(self):
        from core.tutoring.context import truncate_history

        assert truncate_history([]) == []
        assert truncate_history(None) == []


class TestSnapshotTopN:
    """掌握度快照 top-N"""

    def _snap(self):
        return [
            {"kp_key": "k1", "label": "强项", "mastery_level": 90},
            {"kp_key": "k2", "label": "弱项", "mastery_level": 30},
            {"kp_key": "k3", "label": "中等", "mastery_level": 60},
        ]

    def test_weak_first_ordering(self):
        """薄弱(掌握度低)知识点排在前面,模型优先关注"""
        from core.tutoring.context import snapshot_top_n

        result = snapshot_top_n(self._snap(), top_n=3)
        labels = [getattr(s, "label", None) or s.get("label") for s in result]
        assert labels == ["弱项", "中等", "强项"]

    def test_capped_at_top_n(self):
        from core.tutoring.context import snapshot_top_n

        result = snapshot_top_n(self._snap(), top_n=2)
        assert len(result) == 2

    def test_empty(self):
        from core.tutoring.context import snapshot_top_n

        assert snapshot_top_n([]) == []


class TestModelRouting:
    """decide/generate 按配置取模型"""

    def test_get_decide_llm_from_settings(self):
        from config.settings import settings
        from core.tutoring.context import get_decide_llm

        llm = get_decide_llm()
        assert llm is not None
        assert getattr(llm, "model_name", None) == settings.TUTORING_DECIDE_MODEL

    def test_get_generate_llm_from_settings(self):
        from config.settings import settings
        from core.tutoring.context import get_generate_llm

        llm = get_generate_llm()
        assert llm is not None
        assert getattr(llm, "model_name", None) == settings.TUTORING_GENERATE_MODEL
