"""
A2 rewrite 改写测试 - core/rag/query.py rewrite_query

覆盖(tasks E 组"rewrite 测试: 口语改写/失败回退"):
- 正常改写: 口语 → 检索式查询(LLM 返回改写文本)
- 空返回: LLM 返回空 → 原问题兜底
- 异常: LLM 抛异常 → 原问题兜底
- anchor 上下文传入: 改写 prompt 含模块锚点
- history 截断: 只传最近 N 轮(联调⑦, 复用 _truncate_history)

Mock 边界 = LLMFactory.create(真实 doubao), monkeypatch 返回 FakeLLM, 不碰真实 LLM。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

from core.rag import query as rag_core
from langchain_core.messages import AIMessage


class _FakeLLM:
    """固定返回改写文本, 记录最后 human prompt(验证 anchor/history 传入)。"""

    def __init__(self, text):
        self.text = text
        self.last_human = ""

    def invoke(self, messages):
        self.last_human = messages[-1].content
        return AIMessage(content=self.text)


@pytest.fixture
def fake_llm(monkeypatch):
    """monkeypatch LLMFactory.create → FakeLLM, 返回实例供断言"""
    holder = {}

    def _create(*a, **k):
        llm = _FakeLLM("RAG 多路召回 怎么做")
        holder["llm"] = llm
        return llm

    monkeypatch.setattr(rag_core.LLMFactory, "create", _create)
    return holder


class TestRewrite:
    def test_rewrite_success(self, fake_llm):
        """口语 → 检索式改写"""
        out = rag_core.rewrite_query("那套多路召回是怎么搞的？", "rag-system")
        assert out == "RAG 多路召回 怎么做"

    def test_rewrite_empty_fallback(self, monkeypatch):
        """LLM 返回空 → 原问题"""
        monkeypatch.setattr(rag_core.LLMFactory, "create", lambda *a, **k: _FakeLLM(""))
        q = "那套多路召回是怎么搞的？"
        assert rag_core.rewrite_query(q, "rag-system") == q

    def test_rewrite_exception_fallback(self, monkeypatch):
        """LLM 抛异常 → 原问题"""
        def boom(*a, **k):
            raise RuntimeError("doubao down")
        monkeypatch.setattr(rag_core.LLMFactory, "create", boom)
        q = "怎么防学生套答案？"
        assert rag_core.rewrite_query(q, "ai-tutoring") == q

    def test_rewrite_prompt_has_anchor(self, fake_llm):
        """改写 prompt 含模块锚点"""
        rag_core.rewrite_query("怎么防套答案？", "ai-tutoring")
        assert "模块锚点：ai-tutoring" in fake_llm["llm"].last_human

    def test_rewrite_history_truncated(self, fake_llm):
        """history 截断到最近 N 轮才传入 prompt"""
        history = [{"question": f"q{i}", "answer": f"a{i}", "anchor": "ai-tutoring"}
                   for i in range(5)]
        rag_core.rewrite_query("问题", "ai-tutoring", history=history)
        prompt = fake_llm["llm"].last_human
        # 只含最近 N 轮(HISTORY_LIMIT=3): q2/q3/q4, 不含 q0/q1
        assert "q4" in prompt and "q3" in prompt and "q2" in prompt
        assert "q0" not in prompt and "q1" not in prompt

    def test_rewrite_no_history_prompt_ok(self, fake_llm):
        """无 history → prompt 标注无, 不报错"""
        rag_core.rewrite_query("问题", "rag-system", history=[])
        assert "（无）" in fake_llm["llm"].last_human
