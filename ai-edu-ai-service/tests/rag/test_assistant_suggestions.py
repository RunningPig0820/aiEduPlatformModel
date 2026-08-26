"""
A8 suggestions 引导测试 - assistant.gen_suggestions（M6: 底座池约束, 2026-08-26）

覆盖(tasks E 组"引导/池内兜底" + A8 子项 + M6 ②):
- 正常: LLM 生成 1~3 条建议
- 必含 RAG 方向(C5): 提示词约束(prompt 检查) + 输出形状校验
- 可提问范围(M6): 提示词含底座池全部问题逐条列(硬约束不超池)
- 失败兜底: LLM 抛异常 → 池内随机 2 条(≥1 rag), 替换写死静态池
- 形状异常: LLM 输出 0 条/>3 条 → 池内兜底
- 未知模块: anchor 非闭集/空 → FALLBACK_MODULE 池(不崩)
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
from core.rag import guide_pool
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


def _rag_set() -> set:
    return set(guide_pool.GUIDE_POOL["ai-tutoring"]["rag"])


def _scope_set() -> set:
    return set(guide_pool.scope_questions("ai-tutoring"))


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

    def test_prompt_has_scope_pool(self):
        """M6 ②: 提示词含「可提问范围」且逐条列底座池问题(硬约束不超池)"""
        llm = _FakeLLM("随便")
        assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert "可提问范围" in llm.last_system
        pool_q = guide_pool.scope_questions("ai-tutoring")
        assert pool_q[0] in llm.last_system            # 池内首题逐条列出
        assert pool_q[-1] in llm.last_system           # 池内末题也在(非抽样)

    def test_exception_fallback_pool(self):
        """LLM 抛异常 → 池内兜底(≥1 rag, 问题都来自底座池)"""
        class _Boom:
            def invoke(self, m):
                raise RuntimeError("doubao down")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=_Boom())
        assert 1 <= len(out) <= 2
        assert any(q in _rag_set() for q in out)       # rag 方向常驻
        assert all(q in _scope_set() for q in out)     # 不超池

    def test_zero_output_fallback(self):
        """LLM 空输出 → 池内兜底"""
        llm = _FakeLLM("")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert 1 <= len(out) <= 2
        assert any(q in _rag_set() for q in out)

    def test_too_many_lines_fallback(self):
        """LLM 输出 >3 条 → 池内兜底"""
        llm = _FakeLLM("\n".join(f"第{i}条问题？" for i in range(5)))
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert 1 <= len(out) <= 2
        assert any(q in _rag_set() for q in out)

    def test_unknown_module_fallback(self):
        """anchor 非闭集/空 → FALLBACK_MODULE 池(不崩)"""
        llm = _FakeLLM("想了解 RAG 的整体架构吗？")
        out = assistant.gen_suggestions("回答", "", llm=llm)          # anchor 空
        assert len(out) == 1
        llm2 = _FakeLLM("")
        out2 = assistant.gen_suggestions("回答", "unknown-module", llm=llm2)
        assert 1 <= len(out2) <= 2
        assert any(q in _rag_set() for q in out2)

    def test_number_prefix_stripped(self):
        """编号前缀剥离"""
        llm = _FakeLLM("1. 想了解 RAG 的架构吗？\n2. 评测怎么设计的？")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=llm)
        assert not any(s.startswith("1.") or s.startswith("2.") for s in out)
        assert "想了解 RAG 的架构吗？" in out


class TestPoolFallback:
    def test_pool_fallback_has_rag(self):
        """池内兜底: 必含 ≥1 条 rag 组(替换写死静态池)"""
        for _ in range(20):
            out = assistant._pool_fallback("ai-tutoring")
            assert 1 <= len(out) <= 2
            assert any(q in _rag_set() for q in out)
            assert all(q in _scope_set() for q in out)

    def test_pool_fallback_unknown_module(self):
        """未知模块兜底 → FALLBACK 池, 不崩"""
        for _ in range(5):
            out = assistant._pool_fallback("rag-system")
            assert 1 <= len(out) <= 2
