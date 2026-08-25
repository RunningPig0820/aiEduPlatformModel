"""
A7 clarify 澄清轮测试 - assistant.resolve_clarify

覆盖(tasks E 组"clarify 测试: 多候选/澄清一次仍模糊/单候选不触发"):
- 多候选触发: ambiguous & candidates≥2 → clarify 事件{message, candidates, default}
- 单候选不触发: candidates<2 → None(不澄清, 走默认)
- 候选判定: LLM candidates 主源 + 历史锚点兜底 + 仍<2 不触发(C4)
- 最多一轮: 历史末轮是 clarify 轮(answer 空) → 不再二次澄清
- default 绑定: current_project 优先 > 会话最后锚定
- ambiguous=false → None(正常链路)

纯逻辑(无 LLM/COS), 直接测。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

from core.rag import assistant


def _intent(ambiguous=True, candidates=("ai-tutoring", "rag-system"), anchor="ai-tutoring"):
    return {"anchor": anchor, "category": "", "switch_detected": False,
            "ambiguous": ambiguous, "candidates": list(candidates),
            "locked_sections": [], "degraded": False}


class TestResolveClarify:
    def test_multi_candidate_trigger(self):
        """ambiguous & ≥2 候选 → clarify 事件(固定话术 + candidates + default)"""
        ev = assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring", "rag-system")), history=None)
        assert ev is not None
        assert set(("message", "candidates", "default")) <= set(ev)
        assert ev["candidates"] == ["ai-tutoring", "rag-system"]
        assert "rag-system" in ev["message"]  # 话术含 default(缺省 rag-system, 对齐后端契约)

    def test_single_candidate_no_trigger(self):
        """candidates<2 → None(不澄清)"""
        assert assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring",)), history=None) is None

    def test_zero_candidate_history_fallback(self):
        """LLM 未给候选 → 历史锚点兜底(≥2 才触发)"""
        history = [{"question": "q", "answer": "a", "anchor": "ai-tutoring"},
                   {"question": "q", "answer": "a", "anchor": "rag-system"}]
        ev = assistant.resolve_clarify(_intent(candidates=()), history=history)
        assert ev is not None
        assert ev["candidates"] == ["ai-tutoring", "rag-system"]  # 历史锚点兜底

    def test_zero_candidate_history_less_than_2(self):
        """候选兜底后仍 <2 → None"""
        history = [{"question": "q", "answer": "a", "anchor": "ai-tutoring"}]
        assert assistant.resolve_clarify(_intent(candidates=()), history=history) is None

    def test_ambiguous_false_no_trigger(self):
        """ambiguous=false → None(正常链路)"""
        assert assistant.resolve_clarify(_intent(ambiguous=False), history=None) is None

    def test_last_turn_is_clarify_no_second(self):
        """最多一轮: 历史末轮是 clarify 轮(answer 空) → 不再二次澄清"""
        history = [{"question": "q", "answer": "", "anchor": ""}]  # clarify 轮 0 token 无 answer
        assert assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring", "rag-system")), history=history) is None

    def test_last_turn_normal_allows_clarify(self):
        """历史末轮是正常回答轮(answer 非空) → 仍可 clarify"""
        history = [{"question": "q", "answer": "正常回答", "anchor": "ai-tutoring"}]
        ev = assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring", "rag-system")), history=history)
        assert ev is not None

    def test_default_current_project_priority(self):
        """default = current_project 优先"""
        ev = assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring", "rag-system")),
            history=None, current_project="rag-system")
        assert ev["default"] == "rag-system"
        assert "rag-system" in ev["message"]

    def test_default_history_anchor_fallback(self):
        """current_project 非闭集 → 会话最后锚定兜底"""
        history = [{"question": "q", "answer": "a", "anchor": "ai-tutoring"}]
        ev = assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring", "rag-system")),
            history=history, current_project="not-a-module")
        assert ev["default"] == "ai-tutoring"

    def test_default_ai_tutoring_last_resort(self):
        """current_project 非闭集且无历史锚点 → ai-tutoring 兜底"""
        ev = assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring", "rag-system")),
            history=None, current_project="not-a-module")
        assert ev["default"] == "ai-tutoring"

    def test_candidates_dedup(self):
        """candidates 去重保序"""
        ev = assistant.resolve_clarify(
            _intent(candidates=("ai-tutoring", "ai-tutoring", "rag-system")), history=None)
        assert ev["candidates"] == ["ai-tutoring", "rag-system"]


class TestHistoryAnchors:
    def test_dedup_order(self):
        history = [{"anchor": "ai-tutoring"}, {"anchor": "rag-system"}, {"anchor": "ai-tutoring"}]
        assert assistant._history_anchors(history) == ["ai-tutoring", "rag-system"]

    def test_invalid_skipped(self):
        history = [{"anchor": "bad"}, {"anchor": "ai-tutoring"}]
        assert assistant._history_anchors(history) == ["ai-tutoring"]

    def test_empty(self):
        assert assistant._history_anchors([]) == []
        assert assistant._history_anchors(None) == []
