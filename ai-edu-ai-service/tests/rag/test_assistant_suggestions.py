"""
A8 suggestions 引导测试 - assistant.gen_suggestions

覆盖(tasks E 组"引导/静态池兜底" + A8 子项):
- 正常: LLM 生成 1~3 条建议
- 必含 RAG 方向(C5): 提示词约束(prompt 检查) + 输出形状校验
- 失败兜底: LLM 抛异常 → 静态池(含 RAG 方向常驻)
- 形状异常: LLM 输出 0 条/>3 条 → 静态池兜底
- 输出清洗: 编号前缀被剥离

Mock 边界 = llm 注入(FakeLLM), 不碰真实 doubao。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

from core.rag import assistant
from langchain_core.messages import AIMessage


class _FakeLLM:
    def __init__(self, text):
        self.text = text
        self.last_human = ""
        self.last_system = ""

    def invoke(self, messages):
        self.last_human = messages[-1].content
        self.last_system = messages[0].content if messages else ""
        return AIMessage(content=self.text)


class TestGenSuggestions:
    def test_normal_generates_list(self):
        """LLM 正常返回多行 → 解析为建议列表"""
        llm = _FakeLLM("想了解 RAG 的整体架构吗？\n防套答案的护栏是怎么做的？")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert len(out) == 2
        assert "RAG" in out[0]

    def test_single_suggestion(self):
        """LLM 只给 1 条 → 接受"""
        llm = _FakeLLM("想看看评测体系吗？")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert len(out) == 1

    def test_prompt_forces_rag_direction(self):
        """system prompt 约束必含 RAG 方向(C5)"""
        llm = _FakeLLM("随便")
        assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert "RAG" in llm.last_system
        assert "必须包含至少 1 条 RAG" in llm.last_system

    def test_exception_fallback_static(self):
        """LLM 抛异常 → 静态池兜底"""
        class _Boom:
            def invoke(self, m):
                raise RuntimeError("doubao down")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=_Boom())
        assert out == assistant.STATIC_SUGGESTIONS
        assert any("RAG" in s for s in out)  # RAG 方向常驻

    def test_zero_output_fallback(self):
        """LLM 空输出 → 静态池兜底"""
        llm = _FakeLLM("")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert out == assistant.STATIC_SUGGESTIONS

    def test_too_many_lines_fallback(self):
        """LLM 输出 >3 条 → 静态池兜底"""
        llm = _FakeLLM("\n".join(f"第{i}条问题？" for i in range(5)))
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert out == assistant.STATIC_SUGGESTIONS

    def test_number_prefix_stripped(self):
        """编号前缀剥离"""
        llm = _FakeLLM("1. 想了解 RAG 的架构吗？\n2. 评测怎么设计的？")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert not any(s.startswith("1.") or s.startswith("2.") for s in out)
        assert "想了解 RAG 的架构吗？" in out

    def test_static_pool_has_rag(self):
        """静态池含 RAG 方向常驻(D11)"""
        assert any("RAG" in s for s in assistant.STATIC_SUGGESTIONS)
        assert 1 <= len(assistant.STATIC_SUGGESTIONS) <= 3
