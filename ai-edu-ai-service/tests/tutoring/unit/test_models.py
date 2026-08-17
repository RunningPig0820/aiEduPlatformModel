"""
任务 2: 数据模型 models/tutoring.py 测试

覆盖:
- 2.1 枚举闭集(ActionType / EmotionF7 / MasterySignal / EndReason)
- 2.2 Eval / MasterySignalItem
- 2.3 ActionMeta(组合 + 平铺契约 + Eval/Decision 独立子结构)
- 2.4 DecideRequest / GenerateRequest / KpSnapshot(参数校验)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from pydantic import ValidationError


class TestEnums:
    """2.1 枚举闭集"""

    def test_action_type_closed_set(self):
        from models.tutoring import ActionType

        assert {e.value for e in ActionType} == {
            "hint", "approach", "reveal", "concept", "switch", "end",
        }

    def test_emotion_f7_seven_states(self):
        from models.tutoring import EmotionF7

        assert {e.value for e in EmotionF7} == {
            "NEUTRAL", "CONFUSED", "FRUSTRATED", "ANXIOUS",
            "CONFIDENT", "INTERESTED", "BORED",
        }

    def test_mastery_signal_three_values(self):
        from models.tutoring import MasterySignal

        assert {e.value for e in MasterySignal} == {"mastered", "practicing", "struggling"}

    def test_end_reason_four_values(self):
        from models.tutoring import EndReason

        assert {e.value for e in EndReason} == {
            "COMPLETED", "ANSWER_REVEALED", "ABANDONED", "ROUND_LIMIT",
        }


class TestMasterySignalItem:
    """2.2 MasterySignalItem: 字段 topic_label(题型),不是 kp_label(知识点)"""

    def test_topic_label_field(self):
        """字段名为 topic_label,语义为题型"""
        from models.tutoring import MasterySignalItem

        item = MasterySignalItem(topic_label="鸡兔同笼", signal="practicing")
        assert item.topic_label == "鸡兔同笼"
        assert item.signal.value == "practicing"

    def test_old_kp_label_rejected(self):
        """旧字段名 kp_label 不再接受(topic_label required → 校验失败)"""
        from models.tutoring import MasterySignalItem

        with pytest.raises(ValidationError):
            MasterySignalItem(kp_label="鸡兔同笼", signal="practicing")


class TestActionMeta:
    """2.3 ActionMeta 校验与契约"""

    def _valid_meta(self):
        return {
            "type": "hint",
            "reason": "学生已列方程",
            "eval": {"correct": True, "error_type": None, "emotion": "NEUTRAL", "exercise_complete": False},
            "mastery_signals": [{"topic_label": "鸡兔同笼", "signal": "practicing"}],
            "new_question": None,
            "end_reason": None,
            "summary": None,
            "safety_flag": False,
        }

    def test_valid_meta(self):
        from models.tutoring import ActionMeta

        meta = ActionMeta(**self._valid_meta())
        assert meta.type.value == "hint"
        assert meta.eval.correct is True

    def test_type_must_be_closed_set(self):
        from models.tutoring import ActionMeta

        data = self._valid_meta()
        data["type"] = "直接给答案"  # 非闭集
        with pytest.raises(ValidationError):
            ActionMeta(**data)

    def test_eval_required(self):
        from models.tutoring import ActionMeta

        data = self._valid_meta()
        del data["eval"]
        with pytest.raises(ValidationError):
            ActionMeta(**data)

    def test_type_check_strict(self):
        from models.tutoring import ActionMeta

        data = self._valid_meta()
        # 注: Pydantic v2 对 bool 有宽松转换("yes"/"no"/"on"/"off" 会转 True/False),
        # 用无法转换的值验证类型约束
        data["eval"]["correct"] = "not_a_bool"
        with pytest.raises(ValidationError):
            ActionMeta(**data)

    def test_emotion_must_be_f7(self):
        from models.tutoring import ActionMeta

        data = self._valid_meta()
        data["eval"]["emotion"] = "HAPPY"  # 非 F7 七态
        with pytest.raises(ValidationError):
            ActionMeta(**data)

    def test_serialized_flat_contract(self):
        """model_dump 输出平铺契约(与 api.md 一致):type/eval 等顶层字段"""
        from models.tutoring import ActionMeta

        dumped = ActionMeta(**self._valid_meta()).model_dump()
        assert set(dumped.keys()) == {
            "type", "reason", "question_kps", "eval", "mastery_signals",
            "new_question", "end_reason", "summary", "safety_flag", "degraded",
        }
        # eval 是嵌套子结构
        assert set(dumped["eval"].keys()) == {
            "correct", "error_type", "emotion", "exercise_complete",
        }

    def test_degraded_defaults_false(self):
        """degraded 默认 false(正常路径不发降级信号)"""
        from models.tutoring import ActionMeta

        meta = ActionMeta(**self._valid_meta())
        assert meta.degraded is False

    def test_question_kps_optional(self):
        """question_kps 可空:不传时默认为 None,校验不失败"""
        from models.tutoring import ActionMeta

        meta = ActionMeta(**self._valid_meta())
        assert meta.question_kps is None

    def test_question_kps_kept_on_dump(self):
        """question_kps 有值时 model_dump 保留(前端知识点分析数据源)"""
        from models.tutoring import ActionMeta

        data = self._valid_meta()
        data["question_kps"] = ["二元一次方程组", "一元一次方程"]
        meta = ActionMeta(**data)
        assert meta.model_dump()["question_kps"] == ["二元一次方程组", "一元一次方程"]


class TestIndependentSubStructures:
    """2.3 设计决策 7: Eval 与 Decision 独立子结构(可拆)"""

    def test_eval_standalone(self):
        from models.tutoring import Eval

        ev = Eval(correct=False, emotion="CONFUSED")
        assert ev.error_type is None
        assert ev.exercise_complete is False

    def test_decision_standalone(self):
        from models.tutoring import Decision

        d = Decision(type="end", end_reason="COMPLETED")
        assert d.new_question is None
        assert d.safety_flag is False

    def test_decision_matches_actionmeta_fields(self):
        """Decision 的字段与 ActionMeta 决策部分一致(拆次调用时契约不变)"""
        from models.tutoring import ActionMeta, Decision

        decision_fields = {"type", "new_question", "end_reason", "safety_flag"}
        meta_fields = set(ActionMeta.model_fields.keys())
        assert decision_fields <= meta_fields


class TestChatTurn:
    """10.2 ChatTurn 图片双通道"""

    def test_text_only_turn(self):
        """纯文本消息: content 正常,image_url 为 None(向后兼容)"""
        from models.tutoring import ChatTurn

        t = ChatTurn(role="user", content="鸡兔同笼，共35头94脚，各几只？")
        assert t.image_url is None
        assert t.content == "鸡兔同笼，共35头94脚，各几只？"

    def test_image_turn(self):
        """图片消息: content 可为空,image_url 填 COS 签名 URL"""
        from models.tutoring import ChatTurn

        t = ChatTurn(role="user", content="", image_url="https://cos-xxx/1.jpg")
        assert t.content == ""
        assert t.image_url == "https://cos-xxx/1.jpg"

    def test_tolerates_extra_thinking_field(self):
        """Java 在历史消息上附加 thinking 字段(仅存储/展示用)→ 忽略,校验不失败(extra='ignore' 契约)"""
        from models.tutoring import ChatTurn

        t = ChatTurn.model_validate({
            "role": "user",
            "content": "设鸡有x只",
            "thinking": "学生尝试设未知数",  # Java 附加字段
        })
        assert t.content == "设鸡有x只"
        assert "thinking" not in t.model_fields_set  # 附加字段被忽略,不入模型
        assert not hasattr(t, "thinking")

    def test_extra_thinking_field_in_request_history(self):
        """请求级校验: history 里带 thinking 字段仍合法(decide/generate 请求契约)"""
        from models.tutoring import DecideRequest

        req = DecideRequest(
            history=[
                {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
                {"role": "user", "content": "设鸡有x只", "thinking": "学生列出方程思路"},
            ],
            round_count=1,
            answer_request_count=0,
            mastery_snapshot=[],
            subject_hint="math",
        )
        assert req.history[1].content == "设鸡有x只"
        assert len(req.history) == 2


class TestRequests:
    """2.4 请求模型校验"""

    def _decide_payload(self):
        return {
            "history": [{"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"}, {"role": "user", "content": "设鸡有x只"}],
            "round_count": 2,
            "answer_request_count": 0,
            "mastery_snapshot": [{"kp_key": "http://edukg.org/knowledge/3.1/x", "label": "二元一次方程组", "mastery_level": 50}],
            "subject_hint": "math",
        }

    def test_valid_decide_request(self):
        from models.tutoring import DecideRequest

        req = DecideRequest(**self._decide_payload())
        assert req.round_count == 2
        assert req.subject_hint == "math"

    def test_round_count_negative_rejected(self):
        from models.tutoring import DecideRequest

        data = self._decide_payload()
        data["round_count"] = -1
        with pytest.raises(ValidationError):
            DecideRequest(**data)

    def test_missing_history_rejected(self):
        from models.tutoring import DecideRequest

        data = self._decide_payload()
        del data["history"]
        with pytest.raises(ValidationError):
            DecideRequest(**data)

    def test_valid_generate_request(self):
        from models.tutoring import GenerateRequest

        req = GenerateRequest(
            history=[{"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"}, {"role": "user", "content": "我不会"}],
            subject_hint="math",
            action_type="approach",
        )
        assert req.action_type.value == "approach"

    def test_generate_action_type_closed_set(self):
        from models.tutoring import GenerateRequest

        with pytest.raises(ValidationError):
            GenerateRequest(
                history=[],
                action_type="show_me_the_answer",  # 非闭集
            )
