"""
A1 intent 结构化输出测试 - core/rag/query.py intent 全家桶

覆盖(tasks E 组"intent 测试: 正常/失败兜底/非闭集" + schema 校验 + history 截断):
- intent 正常: LLM 结构化 JSON → anchor/category/switch/ambiguous/candidates 解析 + 节映射
- 失败兜底: _llm_intent 返回 {} → 模块关键词兜底 + degraded 标记
- 非闭集: category 非闭集 → 节级关键词兜底(anchor 仍保留 LLM 闭集值)
- schema 校验: _sanitize_intent anchor 闭集/candidates 去重/布尔强制
- history 截断: 只消费最近 N 轮(联调⑦), 含 clarify 轮
- _extract_json: 容错 ``` 围栏/前后缀

Mock 边界 = _llm_intent(内部真实 doubao), 用 monkeypatch 替换返回固定 dict, 不碰真实 LLM。
classify(既有契约) 不动——本文件只测新增 intent 链。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

from core.rag import query as rag_core


def _intent_dict(**over):
    """构造合法 intent dict(默认闭集内值)"""
    base = {
        "anchor": "ai-tutoring",
        "category": "项目介绍",
        "switch_detected": False,
        "ambiguous": False,
        "candidates": [],
    }
    base.update(over)
    return base


class TestIntentNormal:
    """intent 正常: LLM 结构化输出正确解析"""

    def test_intent_parses_structured(self, monkeypatch):
        """完整字段: anchor/category/switch/ambiguous/candidates + 节映射"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": _intent_dict(
            anchor="rag-system", category="难点",
            switch_detected=True, ambiguous=True,
            candidates=["rag-system", "ai-tutoring"],
        ))
        it = rag_core.intent("这套系统的防作弊怎么做的？", history=[])
        assert it["anchor"] == "rag-system"
        assert it["category"] == "难点"
        assert it["switch_detected"] is True
        assert it["ambiguous"] is True
        assert it["candidates"] == ["rag-system", "ai-tutoring"]
        assert it["locked_sections"] == ["04", "07"]  # 难点 → 04/07 节映射
        assert it["degraded"] is False

    def test_intent_category_maps_sections(self, monkeypatch):
        """闭集类别 → 节映射(项目介绍→01/03, 数据关联→05)"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": _intent_dict(category="项目介绍"))
        assert rag_core.intent("AI答疑是什么", [])["locked_sections"] == ["01", "03"]

        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": _intent_dict(category="数据关联"))
        assert rag_core.intent("掌握度怎么落库", [])["locked_sections"] == ["05"]

    def test_intent_category_other_empty_locked(self, monkeypatch):
        """类别'其他' → 不锁任何节"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": _intent_dict(category="其他"))
        assert rag_core.intent("讲讲天气", [])["locked_sections"] == []


class TestIntentFallback:
    """intent 失败/非闭集 → 关键词兜底 + degraded 标记"""

    def test_intent_llm_fail_fallback(self, monkeypatch):
        """LLM 失败(返回 {}) → 模块+节关键词兜底, degraded=True"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": {})
        it = rag_core.intent("怎么防学生套答案？")
        assert it["anchor"] == "ai-tutoring"      # "学生/套答案" 无模块词→默认当前项目 ai-tutoring
        assert "04" in it["locked_sections"]       # 节级关键词命中 04/07
        assert it["degraded"] is True

    def test_intent_llm_fail_module_keyword(self, monkeypatch):
        """LLM 失败但问题含 RAG 关键词 → anchor 路由 rag-project"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": {})
        it = rag_core.intent("RAG 多路召回是怎么做的？")
        assert it["anchor"] == "rag-system"

    def test_intent_category_non_closed_set(self, monkeypatch):
        """LLM 给了 anchor 但 category 非闭集 → anchor 保留, 节级关键词兜底"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": _intent_dict(
            anchor="ai-tutoring", category="非闭集垃圾"))
        it = rag_core.intent("怎么防学生套答案？")
        assert it["anchor"] == "ai-tutoring"  # anchor 闭集内保留
        assert "04" in it["locked_sections"]    # 类别非闭集 → 节级关键词兜底

    def test_intent_anchor_missing_default_project(self, monkeypatch):
        """LLM 返回空 anchor → 默认当前项目(全池), degraded"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": _intent_dict(anchor=""))
        it = rag_core.intent("随便聊聊", current_project="ai-tutoring")
        assert it["anchor"] == "ai-tutoring"
        assert it["degraded"] is True


class TestSanitizeIntent:
    """schema 校验: anchor 必填模块 id、candidates 闭集去重、switch/ambiguous 布尔"""

    def test_anchor_valid_kept(self):
        s = rag_core._sanitize_intent({"anchor": "rag-system"}, "问题")
        assert s["anchor"] == "rag-system"

    def test_anchor_invalid_fallback_module(self):
        """anchor 非闭集 → 关键词兜底模块"""
        s = rag_core._sanitize_intent({"anchor": "bad-module"}, "RAG 检索怎么做的")
        assert s["anchor"] == "rag-system"

    def test_candidates_closed_set_dedup(self):
        """candidates 只保留闭集内 + 去重"""
        s = rag_core._sanitize_intent(
            {"anchor": "ai-tutoring", "candidates": ["rag-system", "rag-system", "bad", "ai-tutoring"]},
            "问题")
        assert s["candidates"] == ["rag-system", "ai-tutoring"]

    def test_booleans_coerced(self):
        """switch/ambiguous 强制布尔(容忍字符串/数字)"""
        s = rag_core._sanitize_intent(
            {"anchor": "ai-tutoring", "switch_detected": "true", "ambiguous": 1}, "问题")
        assert s["switch_detected"] is True
        assert s["ambiguous"] is True

    def test_none_raw_empty(self):
        s = rag_core._sanitize_intent(None, "问题")
        assert s["anchor"] == ""
        assert s["candidates"] == []


class TestHistoryTruncation:
    """history 显式截断: 只取最近 N 轮(联调⑦), 含 clarify 轮"""

    def test_truncate_last_3(self):
        history = [{"question": f"q{i}", "answer": f"a{i}", "anchor": "ai-tutoring"} for i in range(7)]
        out = rag_core._truncate_history(history)
        assert len(out) == rag_core.HISTORY_LIMIT == 3
        assert out[-1]["question"] == "q6"  # 只留最近 3 轮

    def test_truncate_short_history_noop(self):
        history = [{"question": "q", "answer": "a", "anchor": "ai-tutoring"}]
        assert rag_core._truncate_history(history) == history

    def test_truncate_empty(self):
        assert rag_core._truncate_history(None) == []
        assert rag_core._truncate_history([]) == []

    def test_intent_passes_truncated_history(self, monkeypatch):
        """intent 传给 _llm_intent 的 history 已截断到最近 N 轮"""
        captured = {}

        def fake_llm_intent(q, h, current_project="ai-tutoring"):
            captured["h"] = h
            return _intent_dict()

        monkeypatch.setattr(rag_core, "_llm_intent", fake_llm_intent)
        history = [{"question": f"q{i}", "answer": f"a{i}", "anchor": "ai-tutoring"} for i in range(5)]
        rag_core.intent("问题", history=history)
        assert len(captured["h"]) == rag_core.HISTORY_LIMIT
        assert captured["h"][-1]["question"] == "q4"


class TestExtractJson:
    """_extract_json: 容错 ``` 围栏/前后缀/无 JSON"""

    def test_plain_json(self):
        assert rag_core._extract_json('{"anchor":"ai-tutoring"}') == {"anchor": "ai-tutoring"}

    def test_fenced_json(self):
        text = '```json\n{"anchor": "rag-system", "ambiguous": true}\n```'
        assert rag_core._extract_json(text)["anchor"] == "rag-system"

    def test_with_prefix_suffix(self):
        text = '好的，这是结果：{"anchor": "ai-tutoring"} 以上。'
        assert rag_core._extract_json(text)["anchor"] == "ai-tutoring"

    def test_no_json_returns_none(self):
        assert rag_core._extract_json("抱歉我不理解") is None
        assert rag_core._extract_json("") is None
