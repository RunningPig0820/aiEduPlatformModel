"""
任务 5.3: generator.py 测试

按已放行 action_type 渲染生成规约 → llm.stream() → 事件流(meta/token/done)
(注入假 LLM,断言事件序列与 token 拼接)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest


class _Msg:
    def __init__(self, content):
        self.content = content


class FakeStreamLLM:
    """generate 用假 LLM: stream() 按设置产出 token 或中段抛错"""

    def __init__(self, chunks=None, raise_after=None, error=None):
        self.chunks = chunks or []
        self.raise_after = raise_after
        self.error = error
        self.prompts = []

    def stream(self, prompt):
        self.prompts.append(prompt)
        for i, c in enumerate(self.chunks):
            if self.raise_after is not None and i >= self.raise_after:
                raise self.error
            yield _Msg(c)


def _request(action_type="hint"):
    from models.tutoring import GenerateRequest

    return GenerateRequest(
        history=[
            {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
            {"role": "user", "content": "我不会"},
        ],
        subject_hint="math",
        action_type=action_type,
    )


class TestGenerator:
    def test_yields_meta_then_tokens_then_done(self):
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamLLM(chunks=["思路：", "先设x", "再列方程"])
        events = list(iter_tokens(_request(), llm=fake))

        # meta 先行
        assert events[0]["event"] == "meta"
        assert events[0]["data"]["action_type"] == "hint"
        # token 流
        tokens = [e for e in events if e["event"] == "token"]
        assert "".join(t["data"]["content"] for t in tokens) == "思路：先设x再列方程"
        # done 收尾
        assert events[-1]["event"] == "done"
        assert "model_used" in events[-1]["data"]

    def test_prompt_embeds_action_type_rule(self):
        from core.tutoring.generator import iter_tokens
        from core.tutoring.prompts import GENERATION_RULES

        fake = FakeStreamLLM(chunks=["ok"])
        list(iter_tokens(_request(action_type="approach"), llm=fake))

        assert GENERATION_RULES["approach"] in fake.prompts[0]

    def test_mid_stream_error_raises(self):
        """中段抛错 → 异常向上抛(API 层转 event: error)"""
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamLLM(chunks=["a", "b"], raise_after=1, error=RuntimeError("mid-stream"))

        gen = iter_tokens(_request(), llm=fake)
        first = next(gen)          # meta
        second = next(gen)         # token "a"
        assert first["event"] == "meta"
        assert second["data"]["content"] == "a"
        with pytest.raises(RuntimeError):
            list(gen)              # 继续迭代触发中段错误

    def test_model_used_format(self):
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamLLM(chunks=["x"])
        events = list(iter_tokens(_request(), llm=fake))

        model_used = events[-1]["data"]["model_used"]
        assert "/" in model_used  # provider/model 格式
