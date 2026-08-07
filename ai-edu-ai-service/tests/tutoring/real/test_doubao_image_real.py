"""
任务 10.6: 豆包看图答疑 real 冒烟测试(需要 DOUBAO_API_KEY,无 key 自动 skip)

用真实题图(doubao-seed-2-0-lite-260428)验证看图答疑链路:
- decide: 图片题目 → 合法 ActionMeta(能读到图内知识点)
- generate: 带图 hint 流式 → 引导语非空、不泄答案
"""
import pytest

TEST_IMAGE_URL = "https://ai-edu-1318177119.cos.ap-guangzhou.myqcloud.com/tutoring-test/images/math.png"
MODEL = "doubao-seed-2-0-lite-260428"


def _doubao_llm():
    from core.gateway.factory import LLMFactory

    return LLMFactory.create("doubao", MODEL, temperature=0.3)


def _image_history():
    """Java 发送格式: 首条 user 消息是题目图片,第二条是学生提问"""
    return [
        {"role": "user", "content": "", "image_url": TEST_IMAGE_URL},
        {"role": "user", "content": "老师这题怎么做?"},
    ]


@pytest.mark.requires_doubao
class TestDoubaoImageTutoring:
    """豆包看图答疑冒烟"""

    def test_decide_image_reads_question(self):
        """图片题目 → decide 出合法 ActionMeta,且从图内识别到知识点"""
        from core.tutoring.decider import decide
        from models.tutoring import ActionType, DecideRequest

        req = DecideRequest(
            history=_image_history(),
            round_count=1,
            answer_request_count=0,
            mastery_snapshot=[],
            subject_hint="math",
        )
        meta = decide(req, llm=_doubao_llm())

        assert meta.type in ActionType          # 闭集合法
        assert meta.degraded is False           # 走的正常 function_calling 路径
        assert len(meta.mastery_signals) > 0    # 读到图内知识点(看图能力的证据)

    def test_generate_image_hint_guides(self):
        """带图 hint 流式: meta → token → done;引导语非空"""
        from core.tutoring.generator import iter_tokens
        from models.tutoring import GenerateRequest

        req = GenerateRequest(
            history=_image_history(),
            subject_hint="math",
            action_type="hint",
        )
        events = list(iter_tokens(req, llm=_doubao_llm()))

        assert events[0]["event"] == "meta"
        assert events[-1]["event"] == "done"
        text = "".join(e["data"]["content"] for e in events if e["event"] == "token")
        assert text.strip()  # 引导语非空
        # hint 不得直接泄答案(本图最终是 A 选项,允许提到选项但不应直接说"选A")
        assert not text.replace(" ", "").startswith("选A")