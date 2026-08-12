"""
任务: ark_stream.py 原始方舟 SSE 客户端测试

验证 thinking 展示的技术前提: langchain 流式解析会丢弃 reasoning_content,
必须直连方舟读原始 SSE。本测试覆盖:
- _parse_sse_lines: SSE 行 → delta 提取(reasoning/content/tool_calls)、[DONE]、错误
- messages_to_openai: LangChain 消息 → OpenAI 格式(多模态 content list 透传)
- action_meta_tool: ActionMeta → OpenAI function tool
- doubao_conn: 方舟连接参数(与 LLMFactory 单一来源对齐)
"""
import json
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

from core.tutoring import ark_stream
from core.tutoring.ark_stream import (
    _parse_sse_lines,
    action_meta_tool,
    messages_to_openai,
    doubao_conn,
)


def _sse_data(delta: dict) -> str:
    """构造 SSE data 行(用 json.dumps 避免嵌套转义坑)"""
    return "data: " + json.dumps({"choices": [{"delta": delta}]})


class TestParseSseLines:
    """SSE 行 → delta dict 提取"""

    def test_reasoning_content_extracted(self):
        lines = [
            'data: {"choices":[{"delta":{"reasoning_content":"学生","role":"assistant"}}]}',
            'data: {"choices":[{"delta":{"reasoning_content":"答对"}}]}',
            "data: [DONE]",
        ]
        deltas = list(_parse_sse_lines(lines))
        assert [d["reasoning"] for d in deltas] == ["学生", "答对"]
        assert all(d["content"] is None for d in deltas)
        assert all(d["tool_calls"] is None for d in deltas)

    def test_content_extracted(self):
        lines = [
            'data: {"choices":[{"delta":{"content":"思路"}}]}',
            'data: {"choices":[{"delta":{"content":"："}}]}',
            "data: [DONE]",
        ]
        deltas = list(_parse_sse_lines(lines))
        assert [d["content"] for d in deltas] == ["思路", "："]

    def test_tool_calls_extracted_with_name_and_args(self):
        # 模拟工具参数分片流式到达: 第一片带 name,第二片只追加 arguments
        lines = [
            _sse_data({"tool_calls": [{"index": 0, "function": {"name": "ActionMeta", "arguments": '{"type": "end"'}}]}),
            _sse_data({"tool_calls": [{"index": 0, "function": {"arguments": ',"reason":null}'}}]}),
            "data: [DONE]",
        ]
        deltas = list(_parse_sse_lines(lines))
        tcs = [tc for d in deltas for tc in (d["tool_calls"] or [])]
        assert len(tcs) == 2
        assert tcs[0]["index"] == 0
        assert tcs[0]["name"] == "ActionMeta"
        assert tcs[0]["arguments"] == '{"type": "end"'
        assert tcs[1]["arguments"] == ',"reason":null}'

    def test_ignores_non_data_lines(self):
        lines = [
            "event: ping",
            "",
            'data: {"choices":[{"delta":{"content":"x"}}]}',
            "data: [DONE]",
        ]
        deltas = list(_parse_sse_lines(lines))
        assert [d["content"] for d in deltas] == ["x"]

    def test_finish_reason_error_raises(self):
        lines = ['data: {"choices":[{"finish_reason":"error","delta":{}}]}']
        with pytest.raises(RuntimeError):
            list(_parse_sse_lines(lines))

    def test_top_level_error_raises(self):
        lines = ['data: {"error":{"message":"boom"}}']
        with pytest.raises(RuntimeError):
            list(_parse_sse_lines(lines))


class TestMessagesToOpenai:
    """LangChain 消息 → OpenAI 格式"""

    def test_converts_basic_messages(self):
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

        out = messages_to_openai([
            SystemMessage(content="sys"),
            HumanMessage(content="hi"),
            AIMessage(content="hello"),
        ])
        assert out == [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]

    def test_multimodal_content_list_passthrough(self):
        from langchain_core.messages import HumanMessage

        out = messages_to_openai([
            HumanMessage(content=[
                {"type": "text", "text": "题目"},
                {"type": "image_url", "image_url": {"url": "https://x/y.png"}},
            ])
        ])
        assert out[0]["role"] == "user"
        assert out[0]["content"][1]["type"] == "image_url"


class TestActionMetaTool:
    """ActionMeta → OpenAI function tool(decide function-calling 用)"""

    def test_tool_shape(self):
        tool = action_meta_tool()
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "ActionMeta"
        assert tool["function"]["parameters"]["type"] == "object"
        props = tool["function"]["parameters"]["properties"]
        assert "type" in props
        assert "eval" in props


class TestDoubaoConn:
    """方舟连接参数与 LLMFactory 单一来源对齐"""

    def test_conn_matches_factory(self):
        from config.settings import settings
        from core.gateway.factory import LLMFactory

        conn = doubao_conn("doubao-seed-2-0-lite-260428", 0.3)
        assert conn["api_base"] == LLMFactory.PROVIDER_CONFIGS["doubao"]["api_base"]
        assert conn["api_key"] == settings.DOUBAO_API_KEY
        assert conn["model"] == "doubao-seed-2-0-lite-260428"
        assert conn["temperature"] == 0.3
