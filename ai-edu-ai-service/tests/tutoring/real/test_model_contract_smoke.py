"""
任务 1.3: deepseek-v4-flash 模型契约冒烟测试 (spike)

目的: 实测 deepseek-v4-flash 是否支持 function calling / JSON mode,
据此决定 structured.py 的默认降级路径起点 (function_calling vs json_mode)。
参见 design 决策 5。

运行: 需要 DEEPSEEK_API_KEY (无 key 自动 skip)
"""
import json
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from langchain_core.tools import tool


@tool
def answer_action(question: str) -> str:
    """判断学生意图,返回动作类型: hint/approach/reveal/concept/switch/end"""
    return "hint"


def _create_model():
    from core.gateway.factory import LLMFactory

    return LLMFactory.create("deepseek", "deepseek-v4-flash", temperature=0.3)


class TestDeepSeekV4FlashContract:
    """deepseek-v4-flash 契约冒烟测试"""

    @pytest.mark.requires_deepseek
    def test_function_calling_support(self):
        """实测 function calling: 绑定工具后模型是否返回 tool_call"""
        llm = _create_model()
        llm_with_tools = llm.bind_tools([answer_action])
        msg = llm_with_tools.invoke("学生消息: 老师这题答案是多少, 请直接给出动作类型判断")

        print(f"\n[FunctionCalling] content={msg.content!r}")
        print(f"[FunctionCalling] tool_calls={msg.tool_calls!r}")

        if msg.tool_calls:
            print("[VERDICT] function_calling 可用 → structured.py 默认走 function_calling")
        else:
            print("[VERDICT] function_calling 不可用 → structured.py 默认走 json_mode")

        # 冒烟测试: 模型连通即可,能力观察打印供决策
        assert msg.content is not None or msg.tool_calls

    @pytest.mark.requires_deepseek
    def test_json_mode_support(self):
        """实测 JSON mode: response_format=json_object 是否可用"""
        llm = _create_model()
        llm_json = llm.bind(response_format={"type": "json_object"})
        resp = llm_json.invoke('输出JSON对象, 字段: {"type": "hint", "reason": "测试"}')

        print(f"\n[JSONMode] content={resp.content!r}")

        try:
            json.loads(resp.content)
            print("[VERDICT] json_mode 可用 → 作为 function_calling 的兜底")
        except Exception as e:
            print(f"[VERDICT] json_mode 不可用 → {e}, 需要正则提取路径")

        assert resp.content
