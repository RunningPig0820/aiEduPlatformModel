"""
任务 4.1: 视觉题目理解 core/tutoring/question_understand.py 单测

覆盖:
- _parse_labels: 多行拆解(编号/bullet) + 知识点行 + 无法识别 + 上限 5 + 空
- understand_question: 正常 / 空返回 / LLM 异常兜底 / topic_hint 注入(有/无) / 多模态消息结构
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)


class FakeLLM:
    """记录 messages + 返回固定 content 的假 LLM"""

    def __init__(self, content="鸡兔同笼"):
        self.content = content
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return type("Resp", (), {"content": self.content})()


class BoomLLM:
    """抛异常的假 LLM(测兜底)"""

    def invoke(self, messages):
        raise RuntimeError("LLM boom")


def _understand(content=None, llm=None, **req_kwargs):
    """构造请求 + 调用 understand_question,返回 (resp, llm)。"""
    from models.tutoring import QuestionUnderstandRequest
    from core.tutoring.question_understand import understand_question

    req = QuestionUnderstandRequest(image_url="https://cos/signed", **req_kwargs)
    if llm is None:
        llm = FakeLLM(content=content)
    return understand_question(req, llm=llm), llm


class TestParseLabels:
    """_parse_labels 解析"""

    def test_multi_line_with_bullets_and_kp(self):
        from core.tutoring.question_understand import _parse_labels

        text = """1. 鸡兔同笼
- 假设法
• 方程法
知识点：二元一次方程组、假设法"""
        labels, kps = _parse_labels(text)
        assert labels == ["鸡兔同笼", "假设法", "方程法"]
        assert kps == ["二元一次方程组", "假设法"]

    def test_kp_half_width_colon(self):
        from core.tutoring.question_understand import _parse_labels

        labels, kps = _parse_labels("鸡兔同笼\n知识点:一元一次方程")
        assert labels == ["鸡兔同笼"]
        assert kps == ["一元一次方程"]

    def test_unrecognized(self):
        from core.tutoring.question_understand import _parse_labels

        labels, kps = _parse_labels("无法识别")
        assert labels == [] and kps == []

    def test_cap_at_five(self):
        from core.tutoring.question_understand import _parse_labels

        labels, _ = _parse_labels("\n".join(f"题型{i}" for i in range(1, 10)))
        assert len(labels) == 5

    def test_empty_and_blank(self):
        from core.tutoring.question_understand import _parse_labels

        assert _parse_labels("") == ([], [])
        assert _parse_labels("   \n  ") == ([], [])


class TestUnderstandQuestion:
    """understand_question 主流程"""

    def test_normal(self):
        resp, _ = _understand(content="鸡兔同笼\n知识点：二元一次方程组")
        assert resp.topic_labels == ["鸡兔同笼"]
        assert resp.question_kps == ["二元一次方程组"]

    def test_empty_content_fallback(self):
        resp, _ = _understand(content="")
        assert resp.topic_labels == []
        assert resp.question_kps is None

    def test_llm_exception_fallback(self):
        from models.tutoring import QuestionUnderstandRequest
        from core.tutoring.question_understand import understand_question

        req = QuestionUnderstandRequest(image_url="https://cos/signed")
        resp = understand_question(req, llm=BoomLLM())
        assert resp.topic_labels == []
        assert resp.question_kps is None

    def test_topic_hint_injected(self):
        _, llm = _understand(topic_hint=["鸡兔同笼", "相遇问题"])
        system = llm.messages[0].content
        assert "参考题型名" in system
        assert "鸡兔同笼" in system and "相遇问题" in system

    def test_no_topic_hint_no_word_bank(self):
        _, llm = _understand()
        system = llm.messages[0].content
        assert "参考题型名" not in system

    def test_image_url_multimodal(self):
        _, llm = _understand()
        parts = {p.get("type"): p for p in llm.messages[1].content}
        assert parts["image_url"]["image_url"]["url"] == "https://cos/signed"
        assert "text" in parts
