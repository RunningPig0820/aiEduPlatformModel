"""
A2b switch 上下文切换测试 - core/rag/assistant.py resolve_switch + last_anchor

覆盖(tasks E 组"switch 测试: 检测/重置上下文/新锚点链路"):
- 检测: switch_detected=true → resolve_switch 返回 {from_anchor, to_anchor, reset=True}
- 未检测: switch_detected=false/缺省 → None(正常链路)
- from_anchor: 取自 history 末轮 anchor; 无 history → current_project
- 新锚点链路: to_anchor = intent.anchor(切换目标)
- reset 语义: reset=True 标记编排器用新锚点 rewrite→recall→generate(轮次计数归 Java)

纯逻辑(无 LLM/COS), 直接测不 mock。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

from core.rag import assistant


def _intent(anchor="rag-project", switch_detected=True):
    return {"anchor": anchor, "switch_detected": switch_detected, "ambiguous": False,
            "candidates": [], "category": "", "locked_sections": [], "degraded": False}


class TestResolveSwitch:
    def test_switch_detected_returns_event(self):
        """switch_detected=true → 返回 {from_anchor, to_anchor, reset}"""
        history = [{"question": "前一轮", "answer": "…", "anchor": "ai-tutoring"}]
        ev = assistant.resolve_switch(_intent(anchor="rag-project"), history)
        assert ev is not None
        assert ev["from_anchor"] == "ai-tutoring"   # 旧锚点(history 末轮)
        assert ev["to_anchor"] == "rag-project"      # 新锚点(intent)
        assert ev["reset"] is True                   # 重置上下文标记

    def test_switch_not_detected_none(self):
        """switch_detected=false → None(正常链路, 不重置)"""
        assert assistant.resolve_switch(_intent(switch_detected=False), []) is None
        assert assistant.resolve_switch(_intent(switch_detected=False), [
            {"question": "q", "answer": "a", "anchor": "ai-tutoring"}]) is None

    def test_switch_no_history_from_default(self):
        """无 history → from_anchor 用 current_project"""
        ev = assistant.resolve_switch(_intent(), history=None, current_project="ai-tutoring")
        assert ev["from_anchor"] == "ai-tutoring"

    def test_switch_history_last_anchor(self):
        """history 多轮 → 取末轮 anchor 作 from_anchor"""
        history = [
            {"question": "q1", "answer": "a1", "anchor": "ai-tutoring"},
            {"question": "q2", "answer": "a2", "anchor": "rag-project"},
        ]
        ev = assistant.resolve_switch(_intent(anchor="knowledge-graph"), history)
        assert ev["from_anchor"] == "rag-project"

    def test_switch_history_last_no_anchor_uses_default(self):
        """history 末轮缺 anchor → 回落 current_project"""
        history = [{"question": "q", "answer": "a"}]  # 无 anchor 字段
        ev = assistant.resolve_switch(_intent(), history, current_project="ai-tutoring")
        assert ev["from_anchor"] == "ai-tutoring"

    def test_switch_intent_none_safe(self):
        """intent_result None → 不切换(安全兜底)"""
        assert assistant.resolve_switch(None, []) is None

    def test_switch_new_anchor_pipeline(self):
        """新锚点链路: to_anchor 直接来自 intent.anchor(rewrite/recall 用)"""
        ev = assistant.resolve_switch(_intent(anchor="rag-project"), [])
        # to_anchor 落 rag-project → 后续 rewrite_query(..., anchor="rag-project") 走新模块语料池
        assert ev["to_anchor"] == "rag-project"


class TestLastAnchor:
    def test_last_anchor_from_history(self):
        assert assistant.last_anchor([{"anchor": "ai-tutoring"}], "ai-tutoring") == "ai-tutoring"

    def test_last_anchor_invalid_uses_default(self):
        """history 末轮 anchor 非闭集 → current_project"""
        assert assistant.last_anchor([{"anchor": "bad-module"}], "ai-tutoring") == "ai-tutoring"

    def test_last_anchor_empty_history(self):
        assert assistant.last_anchor([], "ai-tutoring") == "ai-tutoring"
        assert assistant.last_anchor(None, "rag-project") == "rag-project"
