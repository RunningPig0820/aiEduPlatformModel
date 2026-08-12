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


# ============ iter_decide_events 流式决策(thinking 展示) ============


class _FakeStreamer:
    """decide 流式用假 streamer: 按设置 yield delta dict 或抛错,记录调用。

    契约: __call__(**kwargs) → iterable of {"reasoning","content","tool_calls"}
    """

    def __init__(self, deltas=None, error=None):
        self.deltas = deltas or []
        self.error = error
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        for d in self.deltas:
            yield d


def _thinking(content):
    return {"reasoning": content, "content": None, "tool_calls": None}


def _delta_content(content):
    return {"reasoning": None, "content": content, "tool_calls": None}


def _tool_delta(arguments, index=0, name="ActionMeta"):
    return {
        "reasoning": None,
        "content": None,
        "tool_calls": [{"index": index, "name": name, "arguments": arguments}],
    }


def _tool_call_deltas(args_dict):
    """完整 tool args 拆两片分片到达(模拟真实流式)"""
    s = json.dumps(args_dict, ensure_ascii=False)
    mid = max(1, len(s) // 2)
    return [_tool_delta(s[:mid]), _tool_delta(s[mid:])]


class TestIterDecideEvents:
    def _req(self, **overrides):
        from models.tutoring import DecideRequest

        base = dict(
            history=[
                {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
                {"role": "user", "content": "设鸡有x只"},
            ],
            round_count=2,
            answer_request_count=0,
            mastery_snapshot=[],
            subject_hint="math",
        )
        base.update(overrides)
        return DecideRequest(**base)

    def test_yields_thinking_then_meta(self):
        """thinking 事件按推理分片流式,meta 从 tool args 解析,thinking 在 meta 前"""
        from core.tutoring.decider import iter_decide_events

        deltas = [_thinking("先判断学生是否答对"), _thinking("答对了")] + _tool_call_deltas(dict(VALID_META_DICT))
        events = list(iter_decide_events(self._req(), streamer=_FakeStreamer(deltas)))

        thinkings = [e for e in events if e["event"] == "thinking"]
        metas = [e for e in events if e["event"] == "meta"]
        assert "".join(t["data"]["content"] for t in thinkings) == "先判断学生是否答对答对了"
        assert len(metas) == 1
        assert metas[0]["data"]["type"] == "hint"  # 来自 VALID_META_DICT
        assert events[0]["event"] == "thinking"
        assert events[-1]["event"] == "meta"

    def test_streamer_receives_openai_messages_and_tool(self):
        """传给 streamer 的是 OpenAI 格式消息 + ActionMeta function tool"""
        from core.tutoring.decider import iter_decide_events

        fs = _FakeStreamer(_tool_call_deltas(dict(VALID_META_DICT)))
        list(iter_decide_events(self._req(), streamer=fs))

        assert len(fs.calls) == 1
        call = fs.calls[0]
        assert call["messages"][0]["role"] == "system"
        assert call["messages"][0]["content"]  # decide 系统提示词非空
        assert call["tools"][0]["function"]["name"] == "ActionMeta"

    def test_is_new_question_short_circuits_no_thinking(self):
        """换题信号短路: 只有 meta(type=switch),无 thinking,streamer 不被调用"""
        from core.tutoring.decider import iter_decide_events

        fs = _FakeStreamer(_tool_call_deltas(dict(VALID_META_DICT)))
        events = list(iter_decide_events(self._req(is_new_question=True), streamer=fs))

        assert len(events) == 1
        assert events[0]["event"] == "meta"
        assert events[0]["data"]["type"] == "switch"
        assert fs.calls == []  # 短路,没走流

    def test_raw_failure_falls_back_to_decide(self):
        """原始流失败 → 降级非流式 decide(llm) → meta 仍合法"""
        from core.tutoring.decider import iter_decide_events

        fake_llm = FakeLLM(fc_args=dict(VALID_META_DICT))
        fs = _FakeStreamer(error=RuntimeError("conn down"))
        events = list(iter_decide_events(self._req(), streamer=fs, llm=fake_llm))

        metas = [e for e in events if e["event"] == "meta"]
        assert len(metas) == 1
        assert metas[0]["data"]["type"] == "hint"
        assert len(fake_llm.prompts) == 1  # 降级走了 decide()

    def test_tool_args_invalid_falls_back(self):
        """tool args 非法(非 JSON/校验失败)→ 降级 decide(llm),不抛异常"""
        from core.tutoring.decider import iter_decide_events

        fake_llm = FakeLLM(fc_args=dict(VALID_META_DICT))
        fs = _FakeStreamer([_tool_delta("not-json{{{")])
        events = list(iter_decide_events(self._req(), streamer=fs, llm=fake_llm))

        metas = [e for e in events if e["event"] == "meta"]
        assert metas[0]["data"]["type"] == "hint"
        assert len(fake_llm.prompts) == 1

    def test_content_json_without_tool_call_parsed(self):
        """模型未走 tool_call、直接吐 ActionMeta JSON → 直接解析,不降级(实测 doubao 偶发)"""
        from core.tutoring.decider import iter_decide_events

        fake_llm = FakeLLM(fc_args=dict(VALID_META_DICT))
        s = json.dumps(dict(VALID_META_DICT), ensure_ascii=False)
        fs = _FakeStreamer([_thinking("推理中"), _delta_content(s)])
        events = list(iter_decide_events(self._req(), streamer=fs, llm=fake_llm))

        thinkings = [e for e in events if e["event"] == "thinking"]
        metas = [e for e in events if e["event"] == "meta"]
        assert "".join(t["data"]["content"] for t in thinkings) == "推理中"
        assert metas[0]["data"]["type"] == "hint"
        assert len(fake_llm.prompts) == 0  # 未降级,没调 decide()

    def test_content_json_chinese_emotion_normalized(self):
        """content 兜底遇中文 emotion('困惑') → 归一化成功,不降级、reason 保留

        2026-08 关思考后 mini 偶发: 模型把 emotion 填中文/小写,且直接吐 content
        (不走 tool_call)。decider 的 content 兜底必须同样归一化,否则触发降级
        → 丢失原始 reason/mastery_signals。
        """
        from core.tutoring.decider import iter_decide_events

        fake_llm = FakeLLM(fc_args=dict(VALID_META_DICT))
        content = json.dumps({
            "type": "approach",
            "reason": "学生询问该题的解法,需提供解题思路大纲",
            "eval": {"correct": False, "error_type": None, "emotion": "困惑", "exercise_complete": False},
            "mastery_signals": [{"kp_label": "基本不等式求最值", "signal": "practicing"}],
            "new_question": None, "end_reason": None, "summary": None, "safety_flag": False,
        }, ensure_ascii=False)
        fs = _FakeStreamer([_delta_content(content)])
        events = list(iter_decide_events(self._req(), streamer=fs, llm=fake_llm))

        metas = [e for e in events if e["event"] == "meta"]
        assert metas[0]["data"]["type"] == "approach"
        assert metas[0]["data"]["eval"]["emotion"] == "CONFUSED"  # 归一化
        assert metas[0]["data"]["reason"] == "学生询问该题的解法,需提供解题思路大纲"  # reason 保留
        assert len(metas[0]["data"]["mastery_signals"]) == 1      # mastery_signals 保留
        assert len(fake_llm.prompts) == 0  # 未降级

    def test_content_json_question_kps_kept(self):
        """content 兜底流式路径 question_kps 字段透传到 meta(前端知识点分析数据源)"""
        from core.tutoring.decider import iter_decide_events

        fake_llm = FakeLLM(fc_args=dict(VALID_META_DICT))
        content = json.dumps({
            "type": "hint",
            "reason": "学生已列出方程",
            "question_kps": ["二元一次方程组", "一元一次方程"],
            "eval": {"correct": True, "error_type": None, "emotion": "NEUTRAL", "exercise_complete": False},
            "mastery_signals": [],
            "new_question": None, "end_reason": None, "summary": None, "safety_flag": False,
        }, ensure_ascii=False)
        fs = _FakeStreamer([_delta_content(content)])
        events = list(iter_decide_events(self._req(), streamer=fs, llm=fake_llm))

        metas = [e for e in events if e["event"] == "meta"]
        assert metas[0]["data"]["type"] == "hint"
        assert metas[0]["data"]["question_kps"] == ["二元一次方程组", "一元一次方程"]
        assert len(fake_llm.prompts) == 0  # 未降级
