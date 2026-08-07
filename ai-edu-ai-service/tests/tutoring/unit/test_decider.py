"""
任务 5.2: decider.py 测试

组装上下文 → 渲染 decide prompt → structured 调用 → ActionMeta
(注入假 LLM,断言 prompt 含截断历史 / snapshot label / 降级兜底)
"""
import json
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest


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


class _Msg:
    def __init__(self, content=""):
        self.content = content
        self.tool_calls = []


class _ToolMsg(_Msg):
    def __init__(self, args):
        super().__init__()
        self.tool_calls = [{"name": "ActionMeta", "args": args, "id": "call_1", "type": "tool_call"}]


class _Bound:
    def __init__(self, llm):
        self.llm = llm

    def _text_of(self, prompt):
        """structured 消息化后输入是消息列表,提取全部文本便于断言"""
        if not isinstance(prompt, (list, tuple)):
            return prompt
        parts = []
        for m in prompt:
            content = getattr(m, "content", "") or ""
            if isinstance(content, str):
                parts.append(content)
            elif isinstance(content, list):
                # 多模态: content=[{type:text},{type:image_url}],只取 text 部分
                parts.append(" ".join(
                    p.get("text", "") for p in content if isinstance(p, dict)
                ))
        return "\n".join(parts)

    def invoke(self, prompt):
        self.llm.prompts.append(self._text_of(prompt))
        if self.llm.fc_raises:
            raise self.llm.fc_raises
        if self.llm.fc_args is not None:
            return _ToolMsg(self.llm.fc_args)
        return _Msg()


class FakeLLM:
    """decide 用假 LLM: 记录 prompt,按设置返回 tool_call 或失败"""

    def __init__(self, fc_args=None, fc_raises=None, json_contents=None, text_raises=None):
        self.fc_args = fc_args
        self.fc_raises = fc_raises
        self.json_contents = list(json_contents or [])
        self.text_raises = text_raises
        self.prompts = []

    def bind_tools(self, tools):
        return _Bound(self)

    def bind(self, **kwargs):
        return _JsonBound(self)

    def invoke(self, prompt):
        self.prompts.append(prompt)
        if self.text_raises:
            raise self.text_raises
        return _Msg(self.json_contents.pop(0) if self.json_contents else "{}")


class _JsonBound:
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, prompt):
        self.llm.prompts.append(prompt)
        if self.llm.json_contents:
            return _Msg(self.llm.json_contents.pop(0))
        return _Msg("{}")


def _request(history=None, mastery_snapshot=None):
    from models.tutoring import DecideRequest

    return DecideRequest(
        history=history or [
            {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
            {"role": "user", "content": "设鸡有x只"},
        ],
        round_count=2,
        answer_request_count=0,
        mastery_snapshot=mastery_snapshot or [],
        subject_hint="math",
    )


class TestNewQuestionSignal:
    """Java 换题信号 is_new_question 短路 switch(2026-08 后端联调定稿)"""

    def _req(self, is_new_question=False):
        from models.tutoring import DecideRequest

        return DecideRequest(
            history=[{"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"}],
            round_count=1,
            answer_request_count=0,
            mastery_snapshot=[],
            subject_hint="math",
            is_new_question=is_new_question,
        )

    def test_new_question_short_circuits_switch(self):
        """is_new_question=true → 直接 switch,不调 LLM"""
        from core.tutoring.decider import decide

        fake = FakeLLM(fc_args=dict(VALID_META_DICT))
        result = decide(self._req(is_new_question=True), llm=fake)

        assert result.type.value == "switch"
        assert len(fake.prompts) == 0  # 短路,没调 LLM

    def test_not_new_question_normal_path(self):
        """is_new_question=false(默认)→ 走正常决策"""
        from core.tutoring.decider import decide

        fake = FakeLLM(fc_args=dict(VALID_META_DICT))
        result = decide(self._req(), llm=fake)

        assert result.type.value == "hint"  # 来自 fake 的正常路径
        assert len(fake.prompts) == 1


class TestDecider:
    def test_decide_returns_actionmeta(self):
        from core.tutoring.decider import decide
        from models.tutoring import ActionMeta

        fake = FakeLLM(fc_args=dict(VALID_META_DICT))
        result = decide(_request(), llm=fake)

        assert isinstance(result, ActionMeta)
        assert result.type.value == "hint"

    def test_decide_truncates_history(self):
        """历史被截断: 最老的第0条不在 prompt,最新的第29条在"""
        from core.tutoring.decider import decide

        long_history = [{"role": "user", "content": f"第{i}条"} for i in range(30)]
        fake = FakeLLM(fc_args=dict(VALID_META_DICT))
        decide(_request(history=long_history), llm=fake)

        prompt = fake.prompts[0]
        assert "第0条" not in prompt
        assert "第29条" in prompt

    def test_decide_injects_snapshot_labels(self):
        """掌握度快照 label 注入 prompt(接地)"""
        from core.tutoring.decider import decide

        fake = FakeLLM(fc_args=dict(VALID_META_DICT))
        decide(
            _request(mastery_snapshot=[
                {"kp_key": "k1", "label": "二元一次方程组", "mastery_level": 50},
            ]),
            llm=fake,
        )

        assert "二元一次方程组" in fake.prompts[0]

    def test_decide_graceful_on_llm_failure(self):
        """LLM 全失败 → 兜底 ActionMeta(type=hint),不抛异常"""
        from core.tutoring.decider import decide
        from models.tutoring import ActionType

        fake = FakeLLM(fc_raises=RuntimeError("fc down"))
        result = decide(_request(), llm=fake)

        assert result.type == ActionType.HINT

    def test_decide_graceful_on_failed_validation(self):
        """LLM 返回非法 tool_call args → 降级到 json mode → 成功"""
        from core.tutoring.decider import decide

        bad_args = {"type": "not_real"}
        good_json = json.dumps(VALID_META_DICT)
        fake = FakeLLM(fc_args=bad_args, json_contents=[good_json])

        result = decide(_request(), llm=fake)

        assert result.type.value == "hint"
