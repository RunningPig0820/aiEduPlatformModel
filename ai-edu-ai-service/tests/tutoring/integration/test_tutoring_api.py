"""
任务 6: tutoring API 端点集成测试

TestClient 调用真实端点 + monkeypatch LLM(不真实调用模型):
- decide: 403(缺/错 token)、422(参数非法)、200(合法 ActionMeta)
- generate: 422(action_type 非闭集)、200(SSE meta/token/done)
"""
import json
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi.testclient import TestClient

from config.settings import settings


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


# ============ 假 LLM ============

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
        return _ToolMsg(self.llm.fc_args) if self.llm.fc_args is not None else _Msg()


class FakeDecideLLM:
    """decide 用假 LLM: bind_tools 返回固定 ActionMeta args"""

    def __init__(self, fc_args=None):
        self.fc_args = fc_args

    def bind_tools(self, tools):
        return _Bound(self)


class FakeStreamLLM:
    """generate 用假 LLM: stream() 返回固定 token"""

    def __init__(self, chunks=None):
        self.chunks = chunks or []

    def stream(self, prompt):
        for c in self.chunks:
            yield _Msg(c)


# ============ 夹具 ============

@pytest.fixture(scope="module")
def client():
    from main import app

    return TestClient(app)


def _headers(token=None):
    token = token if token is not None else settings.INTERNAL_TOKEN
    return {"x-internal-token": token}


def decide_payload(**overrides):
    base = {
        "history": [
            {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
            {"role": "user", "content": "设鸡有x只"},
        ],
        "round_count": 2,
        "answer_request_count": 0,
        "mastery_snapshot": [],
        "subject_hint": "math",
    }
    base.update(overrides)
    return base


def generate_payload(**overrides):
    base = {
        "history": [
            {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
            {"role": "user", "content": "我不会"},
        ],
        "subject_hint": "math",
        "action_type": "approach",
    }
    base.update(overrides)
    return base


class TestDecideEndpoint:
    """POST /api/tutoring/decide"""

    def test_missing_token_403(self, client):
        r = client.post("/api/tutoring/decide", json=decide_payload())
        assert r.status_code == 403

    def test_wrong_token_403(self, client):
        r = client.post("/api/tutoring/decide", json=decide_payload(), headers=_headers("wrong-token"))
        assert r.status_code == 403

    def test_invalid_params_422(self, client):
        r = client.post("/api/tutoring/decide", json=decide_payload(round_count=-1), headers=_headers())
        assert r.status_code == 422

    def test_valid_returns_actionmeta(self, client, monkeypatch):
        monkeypatch.setattr(
            "core.tutoring.decider.get_decide_llm",
            lambda: FakeDecideLLM(fc_args=dict(VALID_META_DICT)),
        )
        r = client.post("/api/tutoring/decide", json=decide_payload(), headers=_headers())
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "hint"
        assert data["eval"]["correct"] is True

    def test_llm_failure_falls_back_to_hint(self, client, monkeypatch):
        """LLM 全段失败 → 四段降级兜底 type=hint,仍 200(绝不吐畸形)"""
        class FailLLM:
            def bind_tools(self, tools):
                raise RuntimeError("boom")

            def bind(self, **kwargs):
                raise RuntimeError("boom")

            def invoke(self, prompt):
                raise RuntimeError("boom")

        monkeypatch.setattr("core.tutoring.decider.get_decide_llm", lambda: FailLLM())
        r = client.post("/api/tutoring/decide", json=decide_payload(), headers=_headers())
        assert r.status_code == 200
        assert r.json()["type"] == "hint"
        assert r.json()["degraded"] is True  # 兜底信号透传到 Java


class TestGenerateEndpoint:
    """POST /api/tutoring/generate"""

    def test_missing_token_403(self, client):
        r = client.post("/api/tutoring/generate", json=generate_payload())
        assert r.status_code == 403

    def test_invalid_action_type_422(self, client):
        r = client.post(
            "/api/tutoring/generate",
            json=generate_payload(action_type="not_a_real_type"),
            headers=_headers(),
        )
        assert r.status_code == 422

    def test_valid_stream_events(self, client, monkeypatch):
        monkeypatch.setattr(
            "core.tutoring.generator.get_generate_llm",
            lambda: FakeStreamLLM(chunks=["思路", "：先设x"]),
        )
        r = client.post("/api/tutoring/generate", json=generate_payload(), headers=_headers())
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        assert "event: meta" in r.text
        assert "思路" in r.text
        assert "event: done" in r.text

    def test_stream_tokens_concatenated(self, client, monkeypatch):
        monkeypatch.setattr(
            "core.tutoring.generator.get_generate_llm",
            lambda: FakeStreamLLM(chunks=["先", "设x", "再列方程"]),
        )
        r = client.post("/api/tutoring/generate", json=generate_payload(), headers=_headers())
        contents = []
        for line in r.text.splitlines():
            if line.startswith("data: "):
                data = json.loads(line[len("data: "):])
                if "content" in data:
                    contents.append(data["content"])
        assert "".join(contents) == "先设x再列方程"
