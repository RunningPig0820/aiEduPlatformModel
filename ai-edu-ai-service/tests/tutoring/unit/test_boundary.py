"""
任务 8.3: 边界用例(decide 判定)

每种场景 mock LLM 返回预期 ActionMeta,断言 decide 透传正确(字段不丢):
- "我不会"→concept 澄清不终止
- "老师你好"→concept 澄清
- "今天天气"→concept 继续(无关不终止)
- "英语题"→concept 继续(说明只辅导数学,引导回来)
- 贴新题→switch + new_question 透传
- 独立解出→end + COMPLETED 联动
- 高危内容→safety_flag=true
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)


class _Msg:
    def __init__(self, content=""):
        self.content = content
        self.tool_calls = []


class _ToolMsg(_Msg):
    def __init__(self, args):
        super().__init__()
        self.tool_calls = [{"name": "ActionMeta", "args": args, "id": "c1", "type": "tool_call"}]


class _Bound:
    def __init__(self, llm):
        self.llm = llm

    def invoke(self, prompt):
        if self.llm.fc_raises:
            raise self.llm.fc_raises
        if self.llm.fc_args is not None:
            return _ToolMsg(self.llm.fc_args)
        return _Msg()


class FakeLLM:
    def __init__(self, fc_args=None, fc_raises=None):
        self.fc_args = fc_args
        self.fc_raises = fc_raises

    def bind_tools(self, tools):
        return _Bound(self)


def _base_meta(**overrides):
    meta = {
        "type": "hint",
        "reason": "测试",
        "eval": {"correct": False, "error_type": None, "emotion": "NEUTRAL", "exercise_complete": False},
        "mastery_signals": [],
        "new_question": None,
        "end_reason": None,
        "summary": None,
        "safety_flag": False,
    }
    meta.update(overrides)
    return meta


class TestBoundaryScenarios:
    """边界场景: decide 透传正确(字段不丢)"""

    def _decide(self, student_message, meta_dict):
        from core.tutoring.decider import decide
        from models.tutoring import DecideRequest

        req = DecideRequest(
            history=[{"role": "user", "content": student_message}],
            round_count=1,
            answer_request_count=0,
            mastery_snapshot=[],
            subject_hint="math",
        )
        return decide(req, llm=FakeLLM(fc_args=dict(meta_dict)))

    def test_wont_do_concept_not_end(self):
        """'我不会' → type=concept(澄清,不终止)"""
        result = self._decide("我不会", _base_meta(type="concept"))
        assert result.type.value == "concept"

    def test_greeting_concept(self):
        """'老师你好' → concept 澄清"""
        result = self._decide("老师你好", _base_meta(type="concept"))
        assert result.type.value == "concept"

    def test_weather_continue(self):
        """'今天天气' → concept(无关→继续,不终止)"""
        result = self._decide("今天天气怎么样", _base_meta(type="concept"))
        assert result.type.value == "concept"

    def test_english_question_continue(self):
        """英语题 → concept(说明只辅导数学,引导回来,不终止)"""
        result = self._decide("这个英语单词怎么读", _base_meta(type="concept"))
        assert result.type.value == "concept"

    def test_new_question_switch(self):
        """贴新题 → switch + new_question 透传"""
        new_q = "水池蓄水，进水管5小时注满，排水管10小时排空，同时开多久注满？"
        result = self._decide(f"换个题：{new_q}", _base_meta(type="switch", new_question=new_q))
        assert result.type.value == "switch"
        assert result.new_question == new_q

    def test_exercise_complete_end(self):
        """独立解出 → type=end + COMPLETED + exercise_complete=true 联动"""
        result = self._decide(
            "答案是鸡23只，兔12只",
            _base_meta(
                type="end",
                end_reason="COMPLETED",
                eval={"correct": True, "error_type": None, "emotion": "CONFIDENT", "exercise_complete": True},
            ),
        )
        assert result.type.value == "end"
        assert result.end_reason.value == "COMPLETED"
        assert result.eval.correct is True
        assert result.eval.exercise_complete is True

    def test_safety_flag(self):
        """高危内容 → safety_flag=true(拦截由 Java 执行)"""
        result = self._decide("我不想活了", _base_meta(type="concept", safety_flag=True))
        assert result.safety_flag is True
