"""
任务 3: 结构化输出保障 core/tutoring/structured.py 测试

四段降级管线逐段覆盖(mock LLM 各段失败):
① function_calling → ② json_mode → ③ 正则提取+Pydantic → ④ 兜底 hint
外加: schema 纠错重试(不重试 LLM 调用,只修 schema)、兜底必过 Pydantic
"""
import json
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest


# ============ 可控假 LLM ============

class _Msg:
    def __init__(self, content):
        self.content = content


class _ToolMsg:
    """带 tool_calls 的消息"""

    def __init__(self, tool_calls, content=""):
        self.tool_calls = tool_calls
        self.content = content


class _FakeToolBound:
    """bind_tools 返回的 runnable (function calling)"""

    def __init__(self, llm):
        self.llm = llm

    def invoke(self, prompt):
        self.llm.fc_calls += 1
        if self.llm.fc_raises:
            raise self.llm.fc_raises
        if self.llm.fc_args is not None:
            return _ToolMsg([{"name": "ActionMeta", "args": self.llm.fc_args, "id": "call_1", "type": "tool_call"}])
        # 无 tool_call: 模拟关思考后 mini 直接把 ActionMeta JSON 作为 content 返回
        return _ToolMsg([], content=self.llm.fc_content or "")


class _FakeBound:
    """bind(response_format=...) 返回的 runnable (json mode)"""

    def __init__(self, llm):
        self.llm = llm

    def invoke(self, prompt):
        self.llm.json_calls += 1
        self.llm.json_inputs.append(prompt)  # 记录收到的输入(消息列表)
        if self.llm.json_raises:
            raise self.llm.json_raises
        if self.llm.json_contents:
            return _Msg(self.llm.json_contents.pop(0))
        return _Msg("{}")


class FakeLLM:
    """可控假 LLM: 按设置模拟各段成功/失败"""

    def __init__(self, *, fc_args=None, fc_raises=None, fc_content=None,
                 json_contents=None, json_raises=None,
                 text_contents=None, text_raises=None):
        self.fc_args = fc_args  # 传给 ActionMeta tool 的 args(合法或非法 dict)
        self.fc_content = fc_content  # 无 tool_call 时的 content(模型直接吐 JSON)
        self.fc_raises = fc_raises
        self.json_contents = list(json_contents or [])
        self.json_raises = json_raises
        self.text_contents = list(text_contents or [])
        self.text_raises = text_raises
        self.fc_calls = 0
        self.json_calls = 0
        self.json_inputs = []  # 记录 json mode 收到的输入(消息列表)
        self.text_calls = 0

    def bind_tools(self, tools):
        return _FakeToolBound(self)

    def bind(self, **kwargs):
        return _FakeBound(self)

    def invoke(self, prompt):
        self.text_calls += 1
        if self.text_raises:
            raise self.text_raises
        if self.text_contents:
            return _Msg(self.text_contents.pop(0))
        return _Msg("{}")


# ============ 测试数据 ============

VALID_META_DICT = {
    "type": "hint",
    "reason": "学生已列方程",
    "eval": {"correct": True, "error_type": None, "emotion": "NEUTRAL", "exercise_complete": False},
    "mastery_signals": [],
    "new_question": None,
    "end_reason": None,
    "summary": None,
    "safety_flag": False,
}


def make_valid_json():
    return json.dumps(VALID_META_DICT)


def make_bad_json():
    """type 非闭集 + eval 缺字段 → 校验必失败"""
    return json.dumps({
        "type": "直接给答案",
        "reason": "x",
        "eval": {"correct": True, "emotion": "NEUTRAL"},
        "mastery_signals": [],
        "new_question": None,
        "end_reason": None,
        "summary": None,
        "safety_flag": False,
    })


# ============ 用例 ============


class TestStructuredDegradation:
    """四段降级管线"""

    def test_stage1_function_calling_success(self):
        """① bind_tools 直接成功,不进后续段"""
        from core.tutoring.structured import generate_action_meta
        from models.tutoring import ActionMeta

        llm = FakeLLM(fc_args=dict(VALID_META_DICT))

        result = generate_action_meta(llm, "prompt")

        assert isinstance(result, ActionMeta)
        assert result.type.value == "hint"
        assert llm.fc_calls == 1
        assert llm.json_calls == 0
        assert llm.text_calls == 0

    def test_stage1_no_tool_call_degrades(self):
        """① 模型没调工具 → 降级到 ②"""
        from core.tutoring.structured import generate_action_meta

        llm = FakeLLM(fc_args=None,  # 无 tool_call
                      json_contents=[make_valid_json()])

        result = generate_action_meta(llm, "prompt")

        assert result.type.value == "hint"
        assert llm.fc_calls == 1
        assert llm.json_calls == 1

    def test_stage1_content_json_parsed_without_tool_call(self):
        """① 无 tool_call 但 content 是合法 ActionMeta JSON → 第一段直接解析成功

        2026-08 关思考后 mini 偶发: 模型不调工具,直接把 ActionMeta JSON 作为
        content 返回(实测 content 里 reason/mastery_signals 都完整)。此前这段
        content 被丢弃、降级到 ② 重试,导致 reason/mastery_signals 丢失。
        """
        from core.tutoring.structured import generate_action_meta

        content_json = json.dumps({
            "type": "approach",
            "reason": "学生询问该题的解法,需提供解题思路大纲",
            "eval": {"correct": False, "emotion": "NEUTRAL"},
            "mastery_signals": [{"kp_label": "基本不等式求最值", "signal": "practicing"}],
            "new_question": None, "end_reason": None, "summary": None, "safety_flag": False,
        }, ensure_ascii=False)
        llm = FakeLLM(fc_args=None, fc_content=content_json,
                      json_contents=["{}"])  # 若降级到 ②,返回空(证明不该走)

        result = generate_action_meta(llm, "prompt")

        assert result.type.value == "approach"
        assert result.reason == "学生询问该题的解法,需提供解题思路大纲"
        assert len(result.mastery_signals) == 1
        assert llm.json_calls == 0  # 第一段就成功,没降级到 ②

    def test_stage1_invalid_args_degrades(self):
        """① tool_call args 校验失败 → 降级到 ②"""
        from core.tutoring.structured import generate_action_meta

        llm = FakeLLM(fc_args={"type": "not_a_real_type"},  # 非法 args
                      json_contents=[make_valid_json()])

        result = generate_action_meta(llm, "prompt")

        assert result.type.value == "hint"
        assert llm.json_calls == 1

    def test_stage1_fail_stage2_json_success(self):
        """① 失败 → ② json_mode 成功"""
        from core.tutoring.structured import generate_action_meta

        llm = FakeLLM(fc_raises=RuntimeError("fc down"),
                      json_contents=[make_valid_json()])

        result = generate_action_meta(llm, "prompt")

        assert result.type.value == "hint"
        assert llm.fc_calls == 1
        assert llm.json_calls == 1

    def test_stage2_fail_stage3_regex_success(self):
        """①② 失败 → ③ 正则从混杂文本抠 JSON"""
        from core.tutoring.structured import generate_action_meta

        messy = f"好的,这是提示:\n{make_valid_json()}\n—— 以上就是答案"
        llm = FakeLLM(fc_raises=RuntimeError("fc down"),
                      json_raises=RuntimeError("json down"),
                      text_contents=[messy])

        result = generate_action_meta(llm, "prompt")

        assert result.type.value == "hint"
        assert llm.text_calls == 1

    def test_all_fail_fallback_hint(self):
        """四段全失败 → 兜底 ActionMeta(type=hint)"""
        from core.tutoring.structured import generate_action_meta
        from models.tutoring import ActionMeta, ActionType

        llm = FakeLLM(fc_raises=RuntimeError("fc down"),
                      json_raises=RuntimeError("json down"),
                      text_raises=RuntimeError("text down"))

        result = generate_action_meta(llm, "prompt")

        assert isinstance(result, ActionMeta)
        assert result.type == ActionType.HINT
        assert result.degraded is True  # 兜底必须带 degraded 信号(Java 监控用)

    def test_fallback_is_pydantic_valid(self):
        """兜底结果可通过 Pydantic 校验(绝不吐畸形)"""
        from core.tutoring.structured import generate_action_meta
        from models.tutoring import ActionMeta

        llm = FakeLLM(fc_raises=RuntimeError("a"),
                      json_raises=RuntimeError("b"),
                      text_raises=RuntimeError("c"))

        result = generate_action_meta(llm, "prompt")

        ActionMeta.model_validate(result.model_dump())  # 不抛异常即通过


class TestCorrectiveRetry:
    """3.2 schema 解析纠错重试(不重试 LLM 调用,只修 schema)"""

    def test_corrective_fixes_bad_json(self):
        """json 解析失败 → 纠错 prompt → 模型修正后成功"""
        from core.tutoring.structured import generate_action_meta

        llm = FakeLLM(fc_raises=RuntimeError("fc down"),
                      json_contents=[make_bad_json(), make_valid_json()])

        result = generate_action_meta(llm, "prompt")

        assert result.type.value == "hint"
        # 第一次调用 + 一次纠错 = 2 次 json 调用
        assert llm.json_calls == 2


class TestEmotionLenient:
    """3.3 emotion 宽容归一化(2026-08 关思考后,mini 偶发填中文/小写情绪值)

    真实模型把 emotion 填成 '困惑'/'confused' 等,导致整条 ActionMeta 校验失败
    → 纠错重试 → 已填好的 mastery_signals 丢失。修复: 校验前归一化到大写枚举。
    """

    def _parse(self, emotion_value):
        from core.tutoring.structured import _parse_and_validate

        raw = json.dumps({
            "type": "hint",
            "reason": "x",
            "eval": {"correct": True, "emotion": emotion_value},
            "mastery_signals": [{"kp_label": "基本不等式求最值", "signal": "practicing"}],
            "new_question": None, "end_reason": None, "summary": None, "safety_flag": False,
        })
        # correction_llm=None + corrective_retries=0: 不重试,失败即返回 None
        # 若归一化生效则直接成功(不靠重试)
        return _parse_and_validate(raw, correction_llm=None, corrective_retries=0)

    def test_chinese_emotion_normalized(self):
        """'困惑' → CONFUSED,且保留 mastery_signals"""
        meta = self._parse("困惑")
        assert meta is not None
        assert meta.eval.emotion.value == "CONFUSED"
        assert len(meta.mastery_signals) == 1
        assert meta.mastery_signals[0].kp_label == "基本不等式求最值"

    def test_lowercase_emotion_normalized(self):
        """'confused' → CONFUSED"""
        meta = self._parse("confused")
        assert meta is not None
        assert meta.eval.emotion.value == "CONFUSED"

    def test_standard_emotion_unchanged(self):
        """大写枚举值照常通过"""
        meta = self._parse("INTERESTED")
        assert meta is not None
        assert meta.eval.emotion.value == "INTERESTED"

    def test_corrective_retries_bounded(self):
        """纠错有上限,仍失败则继续降级到正则段"""
        from core.tutoring.structured import generate_action_meta

        # 默认 corrective_retries=1,两次都不对 → 降级到正则段
        llm = FakeLLM(fc_raises=RuntimeError("fc down"),
                      json_contents=[make_bad_json(), make_bad_json()],
                      text_contents=[make_valid_json()])

        result = generate_action_meta(llm, "prompt")

        assert result.type.value == "hint"
        assert llm.json_calls == 2  # 首次 + 1 次纠错
        assert llm.text_calls == 1  # 正则段兜住


class TestMultimodalMessages:
    """10.3 structured 消息化: 支持图+文消息列表(看图答疑)"""

    @staticmethod
    def _image_messages():
        from langchain_core.messages import HumanMessage, SystemMessage

        return [
            SystemMessage(content="sys"),
            HumanMessage(content=[
                {"type": "text", "text": "对话内容"},
                {"type": "image_url", "image_url": {"url": "https://cos-xxx/1.jpg"}},
            ]),
        ]

    def test_messages_function_calling_path(self):
        """多模态消息(图+文)走 ①function_calling"""
        from core.tutoring.structured import generate_action_meta
        from models.tutoring import ActionMeta

        llm = FakeLLM(fc_args=dict(VALID_META_DICT))
        result = generate_action_meta(llm, self._image_messages())

        assert isinstance(result, ActionMeta)
        assert result.type.value == "hint"
        assert llm.fc_calls == 1

    def test_messages_json_mode_appends_hint(self):
        """②json_mode 下 _JSON_HINT 以 SystemMessage 追加(不能字符串拼接)"""
        from core.tutoring.structured import generate_action_meta

        llm = FakeLLM(fc_raises=RuntimeError("fc down"),
                      json_contents=[make_valid_json()])
        result = generate_action_meta(llm, self._image_messages())

        assert result.type.value == "hint"
        assert llm.json_calls == 1
        # 收到的是 messages + [SystemMessage(JSON hint)],最后一个是 hint
        last = llm.json_inputs[-1]
        from langchain_core.messages import SystemMessage
        assert isinstance(last[-1], SystemMessage)
        assert "JSON" in last[-1].content

    def test_messages_regex_extract_path(self):
        """多模态消息走 ③正则提取"""
        from core.tutoring.structured import generate_action_meta

        messy = f"前缀说明\n{make_valid_json()}\n结束"
        llm = FakeLLM(fc_raises=RuntimeError("a"),
                      json_raises=RuntimeError("b"),
                      text_contents=[messy])
        result = generate_action_meta(llm, self._image_messages())

        assert result.type.value == "hint"
        assert llm.text_calls == 1

    def test_messages_corrective_keeps_image_context(self):
        """纠错重试把纠错 SystemMessage 追加到原消息(图片保持上下文)"""
        from core.tutoring.structured import generate_action_meta

        llm = FakeLLM(fc_raises=RuntimeError("fc down"),
                      json_contents=[make_bad_json(), make_valid_json()])
        result = generate_action_meta(llm, self._image_messages())

        assert result.type.value == "hint"
        assert llm.json_calls == 2  # 首次 + 1 次纠错
        # 纠错消息 = 原消息(含图) + [SystemMessage(纠错)]
        corrective_input = llm.json_inputs[-1]
        assert len(corrective_input) == len(self._image_messages()) + 1
        assert "不合法" in corrective_input[-1].content
