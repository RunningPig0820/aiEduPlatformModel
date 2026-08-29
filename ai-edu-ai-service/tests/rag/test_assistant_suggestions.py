"""
A8 suggestions 引导测试 - assistant.gen_suggestions（底座池原题, 2026-08-26）

覆盖(tasks E 组"引导/池内原题" + A8 子项):
- 返回池内原题(不 LLM 改编)——用户实测: LLM 改编"换提问方法"偏离池内范围,
  新问题没对应切片 → 匹配不到答案(问题6 翻版)。池内原题 100% 可答
- 必含 ≥1 条 rag 组(C5)
- 去重、数量 2~3 条、不超池
- 未知模块/空 anchor → FALLBACK 池(不崩)
- llm 参数保留签名兼容(不再调用)

Mock 边界: 无 LLM(gen_suggestions 纯池内抽样, 0 token)。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

from core.rag import assistant
from core.rag import guide_pool


def _scope_set() -> set:
    return set(guide_pool.scope_questions("ai-tutoring"))


def _rag_set() -> set:
    return set(guide_pool.GUIDE_POOL["ai-tutoring"]["rag"])


class TestGenSuggestions:
    def test_returns_pool_original(self):
        """结束引导返回池内原题(不 LLM 改编, 100% 可答)"""
        out = assistant.gen_suggestions("回答", "ai-tutoring")
        assert 2 <= len(out) <= 3
        assert all(q in _scope_set() for q in out)      # 不超池

    def test_must_include_rag(self):
        """必含 ≥1 条 rag 组(C5)"""
        for _ in range(20):
            out = assistant.gen_suggestions("回答", "ai-tutoring")
            assert any(q in _rag_set() for q in out)

    def test_dedup(self):
        """池内抽样不重复"""
        for _ in range(20):
            out = assistant.gen_suggestions("回答", "ai-tutoring")
            assert len(out) == len(set(out))

    def test_llm_param_ignored(self):
        """llm 参数不再调用(签名兼容, 不再 LLM 生成)"""
        class _Boom:
            def invoke(self, m):
                raise AssertionError("不应调 LLM")
        out = assistant.gen_suggestions("回答", "ai-tutoring", llm=_Boom())
        assert 2 <= len(out) <= 3
        assert all(q in _scope_set() for q in out)

    def test_unknown_module_fallback(self):
        """anchor 非闭集/空 → FALLBACK 池(不崩, 仍池内原题)"""
        for anchor in ("", "unknown-module"):
            out = assistant.gen_suggestions("回答", anchor)
            assert 2 <= len(out) <= 3
            assert all(q in _scope_set() for q in out)   # 兜底到 ai-tutoring 池

    def test_answer_text_irrelevant(self):
        """answer 内容不再影响(纯池内抽样, 不解析上一轮回答)"""
        out_a = assistant.gen_suggestions("随便什么回答", "ai-tutoring")
        assert 2 <= len(out_a) <= 3


class TestPoolSuggestions:
    def test_pool_suggestions_has_rag(self):
        """池内抽样必含 ≥1 条 rag"""
        for _ in range(20):
            out = assistant._pool_suggestions("ai-tutoring")
            assert 2 <= len(out) <= 3
            assert any(q in _rag_set() for q in out)

    def test_pool_suggestions_unknown_module(self):
        """未知模块抽样 → FALLBACK 池, 不崩(rag-system 已有独立池, 不再是未知模块)"""
        for _ in range(5):
            out = assistant._pool_suggestions("unknown-module")
            assert 2 <= len(out) <= 3
            assert all(q in _scope_set() for q in out)
