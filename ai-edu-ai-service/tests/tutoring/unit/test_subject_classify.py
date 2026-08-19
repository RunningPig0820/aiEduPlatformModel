"""
任务 3.1: subject_classify 核心单测(对齐后端 test.md PSC-001~007)

覆盖:
- _parse_subject: K12 十值 / 大小写宽容 / 多余文字 / 闭集外(geology/空/中文)→ None
- classify_subject: 文本物理→physics、文本数学→math、语文/英语/政治/地理/历史(K12 覆盖)、
  图片多模态(image_url part)、无图纯文本(str 通道)、LLM 异常→空 subject 不抛、
  闭集外→None、模型参数统一(thinking off + 20s + retry 0)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)


class FakeLLM:
    """记录 messages + 返回固定 content 的假 LLM"""

    def __init__(self, content="math"):
        self.content = content
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return type("Resp", (), {"content": self.content})()


class BoomLLM:
    """抛异常的假 LLM(测兜底)"""

    def invoke(self, messages):
        raise RuntimeError("LLM boom")


def _classify(llm=None, content="鸡兔同笼，共35头94脚，各几只？", image_url=None):
    """构造请求 + 调用 classify_subject,返回 (resp, llm)。"""
    from models.tutoring import SubjectClassifyRequest
    from core.tutoring.subject_classify import classify_subject

    req = SubjectClassifyRequest(content=content, image_url=image_url)
    if llm is None:
        llm = FakeLLM()
    return classify_subject(req, llm=llm), llm


class TestParseSubject:
    """_parse_subject 闭集解析"""

    def test_all_ten_k12_values(self):
        from core.tutoring.subject_classify import _parse_subject

        for code in ["math", "physics", "chemistry", "biology",
                     "chinese", "english", "politics", "geography", "history", "other"]:
            assert _parse_subject(code) == code, code

    def test_case_and_whitespace_tolerant(self):
        from core.tutoring.subject_classify import _parse_subject

        assert _parse_subject("  MATH ") == "math"
        assert _parse_subject("Physics") == "physics"

    def test_extra_text_tolerant(self):
        from core.tutoring.subject_classify import _parse_subject

        assert _parse_subject("答案:math") == "math"
        assert _parse_subject("physics。") == "physics"

    def test_out_of_set_none(self):
        from core.tutoring.subject_classify import _parse_subject

        assert _parse_subject("geology") is None   # 闭集外
        assert _parse_subject("astronomy") is None
        assert _parse_subject("") is None
        assert _parse_subject(None) is None
        assert _parse_subject("化学") is None       # 中文名不映射(提示词禁止,闭集外放行)


class TestClassifySubject:
    """classify_subject 主流程"""

    def test_text_physics(self):
        resp, _ = _classify(llm=FakeLLM("physics"), content="物体做自由落体运动，求落地速度")
        assert resp.subject == "physics"

    def test_text_math(self):
        resp, _ = _classify(llm=FakeLLM("math"))
        assert resp.subject == "math"

    def test_k12_subjects_all_recognized(self):
        for code in ["chinese", "english", "politics", "geography", "history", "biology", "chemistry"]:
            resp, _ = _classify(llm=FakeLLM(code))
            assert resp.subject == code, code

    def test_image_multimodal(self):
        """有图 → HumanMessage 含 text + image_url 两个 part,结合图分类"""
        resp, llm = _classify(llm=FakeLLM("physics"), content=None, image_url="https://cos/signed")
        parts = {p.get("type"): p for p in llm.messages[1].content}
        assert parts["image_url"]["image_url"]["url"] == "https://cos/signed"
        assert "text" in parts
        assert resp.subject == "physics"

    def test_text_only_channel(self):
        """无图 → HumanMessage 是纯文本 str,且含题目内容"""
        resp, llm = _classify(llm=FakeLLM("math"))
        assert isinstance(llm.messages[1].content, str)
        assert "鸡兔同笼" in llm.messages[1].content
        assert resp.subject == "math"

    def test_system_prompt_subject_agnostic(self):
        """提示词学科无关 + K12 十值闭集都在 prompt"""
        _, llm = _classify(llm=FakeLLM("math"))
        system = llm.messages[0].content
        for code in ["math", "physics", "chemistry", "biology",
                     "chinese", "english", "politics", "geography", "history", "other"]:
            assert code in system, code
        assert "不解答" in system  # 只判学科不做解题

    def test_llm_exception_fallback(self):
        """LLM 异常 → 空 subject,不抛异常"""
        from models.tutoring import SubjectClassifyRequest
        from core.tutoring.subject_classify import classify_subject

        req = SubjectClassifyRequest(content="任意题")
        resp = classify_subject(req, llm=BoomLLM())
        assert resp.subject is None

    def test_out_of_set_normalized_to_none(self):
        """模型输出闭集外学科(geology)→ 空 subject,不误判为 other"""
        resp, _ = _classify(llm=FakeLLM("geology"))
        assert resp.subject is None


class TestFactoryParams:
    """模型统一 + 慢修复(后端 PSC-005)"""

    def test_factory_doubao_thinking_off_with_timeout(self):
        """不注入 llm 走工厂: doubao mini / 0.3 + thinking disabled + 20s + retry 0"""
        from unittest.mock import patch

        from core.tutoring.subject_classify import (
            _CLASSIFY_MODEL,
            _CLASSIFY_PROVIDER,
            _CLASSIFY_TEMPERATURE,
            classify_subject,
        )
        from models.tutoring import SubjectClassifyRequest

        with patch(
            "core.tutoring.subject_classify.LLMFactory.create",
            return_value=FakeLLM("math"),
        ) as m:
            req = SubjectClassifyRequest(content="鸡兔同笼")
            resp = classify_subject(req)
            assert resp.subject == "math"

        args, kwargs = m.call_args
        assert args == (_CLASSIFY_PROVIDER, _CLASSIFY_MODEL)
        assert kwargs["temperature"] == _CLASSIFY_TEMPERATURE
        assert kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
        assert kwargs["request_timeout"] == 20
        assert kwargs["max_retries"] == 0
