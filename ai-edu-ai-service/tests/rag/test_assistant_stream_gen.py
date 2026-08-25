"""
A5 generate 流式化测试 - assistant.stream_generate

覆盖(tasks E 组"断连取消测试" + A5 子项):
- token 流式增量: content 逐段 yield
- usage 透传: include_usage → 流末尾 usage chunk → {type:usage}
- 超时降级: queue 空转 RAG_GEN_TIMEOUT → 写死话术 + 召回清单, 0 token
- 异常降级: streamer 抛异常 → GEN_FAIL_MSG + 召回清单
- is_disconnected: request 断开 → 中止(不 yield 后续)
- streamer 注入: fake 同步生成器, 不碰真实方舟

Mock 边界 = streamer 注入(fake); 不碰真实 doubao 网络。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import asyncio

import pytest

from core.rag import assistant
from config.settings import settings

HITS = [
    {"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "score": 0.9, "authority": 1.0,
     "source": "完善文档", "file": "04-安全与防作弊", "file_path": "4.完善文档/04-安全与防作弊.md",
     "anchor": "04-安全与防作弊", "summary": "防作弊答案出口机制", "text": "防套答案: 第1次要答案拦下给思路"},
    {"key": "ai-tutoring/语雀-答疑理念/答疑理念#0", "score": 0.7, "authority": 0.7,
     "source": "语雀", "file": "语雀-答疑理念", "file_path": "1.语雀/答疑理念.md",
     "anchor": "答疑理念", "summary": "AI答疑定位与理念", "text": "AI答疑面向小学到高中全学段"},
]


class _FakeStreamer:
    """fake stream_chat: 兼容 stream_generate 的调用签名, 产出预置 delta 序列"""

    def __init__(self, deltas):
        self.deltas = deltas
        self.kwargs = None

    def __call__(self, **kwargs):
        self.kwargs = kwargs
        for d in self.deltas:
            yield d


def _collect(agen, request=None):
    """消费 async generator → 事件列表"""
    async def _run():
        out = []
        async for ev in agen:
            out.append(ev)
        return out
    return asyncio.run(_run())


def _raise_streamer(exc):
    def _f(**kwargs):
        raise exc
    return _f


class TestStreamGenerate:
    def test_token_stream(self):
        """content 逐段 yield token"""
        fs = _FakeStreamer([
            {"reasoning": None, "content": "面试", "tool_calls": None, "usage": None},
            {"reasoning": None, "content": "口述", "tool_calls": None, "usage": None},
        ])
        evs = _collect(assistant.stream_generate(HITS, "AI答疑是什么", streamer=fs))
        tokens = [e["text"] for e in evs if e["type"] == "token"]
        assert tokens == ["面试", "口述"]

    def test_usage_passthrough(self):
        """include_usage → 流末尾 usage chunk → {type:usage}"""
        fs = _FakeStreamer([
            {"reasoning": None, "content": "答案", "tool_calls": None, "usage": None},
            {"reasoning": None, "content": None, "tool_calls": None,
             "usage": {"prompt_tokens": 320, "completion_tokens": 140, "total_tokens": 460}},
        ])
        evs = _collect(assistant.stream_generate(HITS, "问题", streamer=fs))
        usage_evs = [e for e in evs if e["type"] == "usage"]
        assert usage_evs and usage_evs[0]["usage"]["prompt_tokens"] == 320

    def test_streamer_include_usage_requested(self):
        """streamer 收到 include_usage=True + RAG_GEN_TIMEOUT(8s)"""
        fs = _FakeStreamer([{"reasoning": None, "content": "x", "tool_calls": None, "usage": None}])
        _collect(assistant.stream_generate(HITS, "问题", streamer=fs))
        assert fs.kwargs["include_usage"] is True
        assert fs.kwargs["timeout"] == settings.RAG_GEN_TIMEOUT

    def test_streamer_prompt_has_blocks(self):
        """生成 prompt 含检索块上下文(面试口述)"""
        fs = _FakeStreamer([{"reasoning": None, "content": "x", "tool_calls": None, "usage": None}])
        _collect(assistant.stream_generate(HITS, "AI答疑是什么", streamer=fs))
        user_msg = fs.kwargs["messages"][-1]["content"]
        assert "防套答案: 第1次要答案拦下给思路" in user_msg
        assert "AI答疑是什么" in user_msg

    def test_exception_degrade(self):
        """streamer 抛异常 → GEN_FAIL_MSG + 召回清单, 0 token"""
        evs = _collect(assistant.stream_generate(HITS, "问题", streamer=_raise_streamer(RuntimeError("doubao down"))))
        errors = [e for e in evs if e["type"] == "error"]
        assert errors
        assert "生成服务异常" in errors[0]["text"]
        assert "04-安全与防作弊" in errors[0]["text"]      # 召回清单
        assert not any(e["type"] == "token" for e in evs)  # 0 token

    def test_disconnect_aborts(self):
        """首个 token 产出后检测到断开 → 中止, 不 yield 后续 token"""
        fs = _FakeStreamer([
            {"reasoning": None, "content": "开头", "tool_calls": None, "usage": None},
            {"reasoning": None, "content": "结尾", "tool_calls": None, "usage": None},
        ])

        class _Req:
            """有状态断开: 首次查询 False(产出 token), 之后 True(中止)。"""

            def __init__(self):
                self.calls = 0

            async def is_disconnected(self):
                self.calls += 1
                return self.calls >= 2

        evs = _collect(assistant.stream_generate(HITS, "问题", request=_Req(), streamer=fs))
        tokens = [e["text"] for e in evs if e["type"] == "token"]
        assert tokens == ["开头"]           # 只产第一个, 第二次检查断开后中止
        assert "结尾" not in tokens

    def test_no_request_ok(self):
        """无 request(离线/评测) → 不检测断开, 正常流完"""
        fs = _FakeStreamer([{"reasoning": None, "content": "完整答案", "tool_calls": None, "usage": None}])
        evs = _collect(assistant.stream_generate(HITS, "问题", streamer=fs))
        assert [e["text"] for e in evs if e["type"] == "token"] == ["完整答案"]
