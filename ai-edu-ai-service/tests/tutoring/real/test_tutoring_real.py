"""
任务 8.5: real 全流程测试(deepseek-v4-flash,需要 DEEPSEEK_API_KEY,无 key 自动 skip)

发起 → 引导 → 回答 → 换题 → 收尾 → 掌握度信号
"""
import pytest


Q_CHICKEN_RABBIT = "鸡兔同笼，共35头94脚，各几只？"
Q_POOL = "水池蓄水，进水管5小时注满，排水管10小时排空，同时开多久注满？"


def _decide(history, snapshot=None):
    """构造 decide 请求(无 current_question: 题目在 history 中,模型推断)"""
    from models.tutoring import DecideRequest
    from core.tutoring.decider import decide

    req = DecideRequest(
        history=history,
        round_count=2,
        answer_request_count=0,
        mastery_snapshot=snapshot or [
            {"kp_key": "http://edukg.org/knowledge/3.1/x", "label": "二元一次方程组", "mastery_level": 50},
        ],
        subject_hint="math",
    )
    return decide(req)


@pytest.mark.requires_deepseek
class TestTutoringRealFlow:
    """真实模型全流程(边界判定 + 引导 + 换题 + 收尾)"""

    def test_first_question_guides_not_switch(self):
        """B1 修复: 首条消息(只有题目,无老师回复)绝不能是 switch——应引导 hint/approach/concept"""
        meta = _decide([{"role": "user", "content": Q_CHICKEN_RABBIT}])
        assert meta.type.value in {"hint", "approach", "concept", "reveal"}
        assert meta.type.value != "switch"

    def test_ask_for_help_guides_not_ends(self):
        """学生求帮助 → 不应直接 end;应是引导类(concept/hint/approach)"""
        meta = _decide([
            {"role": "user", "content": Q_CHICKEN_RABBIT},
            {"role": "user", "content": "老师我不会，给我讲讲思路吧"},
        ])
        assert meta.type.value in {"concept", "hint", "approach", "reveal"}
        assert meta.type.value != "end"

    def test_unrelated_chatter_ends(self):
        """闲聊(无关)→ end 终止"""
        meta = _decide([
            {"role": "user", "content": Q_CHICKEN_RABBIT},
            {"role": "user", "content": "今天天气怎么样"},
        ])
        assert meta.type.value == "end"

    def test_switch_on_new_question(self):
        """对话中贴新题 → switch + new_question(换题判定由 Python 从 history 推断)"""
        history = [
            {"role": "user", "content": Q_CHICKEN_RABBIT},
            {"role": "ai", "content": "先找已知条件，能列出来吗？"},
            {"role": "user", "content": f"换一道题吧：{Q_POOL}"},
        ]
        meta = _decide(history)
        assert meta.type.value == "switch"
        assert meta.new_question

    def test_generate_hint_no_final_answer(self):
        """generate(hint) 流式 → 正文不含最终数值答案(引导性反问)"""
        from models.tutoring import GenerateRequest
        from core.tutoring.generator import iter_tokens

        req = GenerateRequest(
            history=[
                {"role": "user", "content": Q_CHICKEN_RABBIT},
                {"role": "user", "content": "我不会"},
            ],
            subject_hint="math",
            action_type="hint",
        )
        text = "".join(ev["data"]["content"] for ev in iter_tokens(req) if ev["event"] == "token")
        # hint 不得直接泄露最终答案(鸡23 兔12)
        assert "23" not in text and "12" not in text
