"""
任务 5.3: generator.py 测试

按已放行 action_type 渲染生成规约 → 原始方舟流式 → 事件流(meta/thinking/token/done)
(注入假 streamer,断言事件序列、thinking 穿插与 token 拼接)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest


def _delta(content=None, reasoning=None):
    """构造方舟 delta dict(reasoning/content/tool_calls 固定结构)"""
    return {"reasoning": reasoning, "content": content, "tool_calls": None}


class FakeStreamer:
    """generate 用假 streamer: __call__(**kwargs) → iterable of delta dict。

    契约与 core.tutoring.ark_stream.stream_chat 一致(连接参数忽略,测试不联网)。
    """

    def __init__(self, deltas=None, raise_after=None, error=None):
        self.deltas = deltas or []
        self.raise_after = raise_after
        self.error = error
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        for i, d in enumerate(self.deltas):
            if self.raise_after is not None and i >= self.raise_after:
                raise self.error
            yield d


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


def _system_text(call):
    """从传给 streamer 的 OpenAI 消息里取 system 提示词(便于断言 prompt 内容)"""
    return call["messages"][0]["content"]


class TestGenerator:
    def test_yields_meta_then_tokens_then_done(self):
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamer(deltas=[_delta(content="思路："), _delta(content="先设x"), _delta(content="再列方程")])
        events = list(iter_tokens(_request(), streamer=fake))

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

        fake = FakeStreamer(deltas=[_delta(content="ok")])
        list(iter_tokens(_request(action_type="approach"), streamer=fake))

        assert GENERATION_RULES["approach"] in _system_text(fake.calls[0])

    def test_thinking_events_interleave_before_tokens(self):
        """推理分片 → thinking 事件;思考在 token 前,meta 在 thinking 前"""
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamer(deltas=[
            _delta(reasoning="先读题"),
            _delta(reasoning="条件不足,引导"),
            _delta(content="这题要先设未知数"),
            _delta(content="再列方程"),
        ])
        events = list(iter_tokens(_request(), streamer=fake))

        thinkings = [e for e in events if e["event"] == "thinking"]
        tokens = [e for e in events if e["event"] == "token"]
        assert "".join(t["data"]["content"] for t in thinkings) == "先读题条件不足,引导"
        assert "".join(t["data"]["content"] for t in tokens) == "这题要先设未知数再列方程"

        def _idx(event):
            return next(i for i, (e, _) in enumerate([(x["event"], x) for x in events]) if e == event)

        assert _idx("meta") < _idx("thinking") < _idx("token") < _idx("done")

    def test_mid_stream_error_raises(self):
        """中段抛错 → 异常向上抛(API 层转 event: error)"""
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamer(deltas=[_delta(content="a"), _delta(content="b")], raise_after=1, error=RuntimeError("mid-stream"))

        gen = iter_tokens(_request(), streamer=fake)
        first = next(gen)          # meta
        second = next(gen)         # token "a"
        assert first["event"] == "meta"
        assert second["data"]["content"] == "a"
        with pytest.raises(RuntimeError):
            list(gen)              # 继续迭代触发中段错误

    def test_model_used_format(self):
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamer(deltas=[_delta(content="x")])
        events = list(iter_tokens(_request(), streamer=fake))

        model_used = events[-1]["data"]["model_used"]
        assert "/" in model_used  # provider/model 格式

    def test_empty_stream_fallback(self):
        """零 token 流(仅思考或无内容)→ 兜底话术(避免学生收到空回复)"""
        from core.tutoring.generator import iter_tokens

        fake = FakeStreamer(deltas=[_delta(reasoning="只在思考")])  # 无 content
        events = list(iter_tokens(_request(), streamer=fake))

        tokens = [e for e in events if e["event"] == "token"]
        assert len(tokens) == 1  # 只有兜底话术
        assert tokens[0]["data"]["content"].strip()
        assert events[-1]["event"] == "done"
