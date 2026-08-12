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


# ============ 假方舟流(替代原始 SSE 客户端,不真实调用模型) ============

class _FakeArkStream:
    """ark_stream.stream_chat 的假实现: 按设置 yield delta dict 或抛错。

    契约: __call__(**kwargs) → iterable of {"reasoning","content","tool_calls"}
    """

    def __init__(self, deltas=None, error=None):
        self.deltas = deltas or []
        self.error = error

    def __call__(self, **kwargs):
        if self.error:
            raise self.error
        for d in self.deltas:
            yield d


def _delta(content=None, reasoning=None, tool_calls=None):
    return {"reasoning": reasoning, "content": content, "tool_calls": tool_calls}


def _tool_delta(arguments):
    return _delta(tool_calls=[{"index": 0, "name": "ActionMeta", "arguments": arguments}])


def _meta_tool_deltas(args_dict):
    """完整 ActionMeta args 拆两片分片到达(模拟真实流式)"""
    s = json.dumps(args_dict, ensure_ascii=False)
    mid = max(1, len(s) // 2)
    return [_tool_delta(s[:mid]), _tool_delta(s[mid:])]


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


def _parse_sse(text):
    """解析 SSE 文本为 [(event, data_dict), ...]"""
    events = []
    for block in text.split("\n\n"):
        event = None
        data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: "):])
        if event:
            events.append((event, data))
    return events


def _meta_from_sse(text):
    """从 SSE 文本提取 meta 事件的 data(ActionMeta)"""
    for event, data in _parse_sse(text):
        if event == "meta":
            return data
    raise AssertionError("SSE 中无 meta 事件")


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

    def test_valid_returns_actionmeta_stream(self, client, monkeypatch):
        """decide 流式: SSE 含 agent 阶段 + thinking + meta(ActionMeta) + done"""
        monkeypatch.setattr(
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(deltas=_meta_tool_deltas(dict(VALID_META_DICT))),
        )
        r = client.post("/api/tutoring/decide", json=decide_payload(), headers=_headers())
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        data = _meta_from_sse(r.text)
        assert data["type"] == "hint"
        assert data["eval"]["correct"] is True

    def test_decide_streams_thinking_before_meta(self, client, monkeypatch):
        """thinking 事件流式出现,且在 meta 之前"""
        monkeypatch.setattr(
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(deltas=[
                _delta(reasoning="判断学生是否正确"),
                _delta(reasoning="正确,收尾"),
                *_meta_tool_deltas(dict(VALID_META_DICT)),
            ]),
        )
        r = client.post("/api/tutoring/decide", json=decide_payload(), headers=_headers())
        events = _parse_sse(r.text)
        thinkings = [e for e, d in events if e == "thinking"]
        meta_idx = next(i for i, (e, d) in enumerate(events) if e == "meta")
        assert len(thinkings) == 2
        assert "".join(d["content"] for e, d in events if e == "thinking") == "判断学生是否正确正确,收尾"
        # 所有 thinking 都在 meta 之前
        assert all(i < meta_idx for i, (e, d) in enumerate(events) if e == "thinking")

    def test_decide_agent_stage_sequence(self, client, monkeypatch):
        """agent 阶段序列: perceive→analyze→plan→decide → meta → done"""
        monkeypatch.setattr(
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(deltas=_meta_tool_deltas(dict(VALID_META_DICT))),
        )
        r = client.post("/api/tutoring/decide", json=decide_payload(), headers=_headers())
        events = _parse_sse(r.text)
        stages = [e[1]["stage"] for e in events if e[0] == "agent"]
        assert stages == ["perceive", "analyze", "plan", "decide"]
        # meta 在 agent 阶段之后,done 收尾
        assert events[-1][0] == "done"

    def test_is_new_question_streams_switch(self, client, monkeypatch):
        """换题信号短路: is_new_question=true 仍流式,meta 带 type=switch,无 thinking"""
        monkeypatch.setattr(
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(deltas=_meta_tool_deltas(dict(VALID_META_DICT))),
        )
        r = client.post(
            "/api/tutoring/decide",
            json=decide_payload(is_new_question=True),
            headers=_headers(),
        )
        assert r.status_code == 200
        events = _parse_sse(r.text)
        data = _meta_from_sse(r.text)
        assert data["type"] == "switch"
        assert "thinking" not in [e for e, d in events]  # 短路不出思考

    def test_llm_failure_falls_back_to_hint(self, client, monkeypatch):
        """原始流失败 + LLM 全段失败 → 四段降级兜底 type=hint,仍 200(绝不吐畸形)"""
        class FailLLM:
            def bind_tools(self, tools):
                raise RuntimeError("boom")

            def bind(self, **kwargs):
                raise RuntimeError("boom")

            def invoke(self, prompt):
                raise RuntimeError("boom")

        # 原始流抛错 → 降级 decide() → get_decide_llm 返回 FailLLM → 四段兜底
        monkeypatch.setattr(
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(error=RuntimeError("conn down")),
        )
        monkeypatch.setattr("core.tutoring.decider.get_decide_llm", lambda: FailLLM())
        r = client.post("/api/tutoring/decide", json=decide_payload(), headers=_headers())
        assert r.status_code == 200
        data = _meta_from_sse(r.text)
        assert data["type"] == "hint"
        assert data["degraded"] is True  # 兜底信号透传到 Java


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
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(deltas=[_delta(content="思路"), _delta(content="：先设x")]),
        )
        r = client.post("/api/tutoring/generate", json=generate_payload(), headers=_headers())
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        assert "event: meta" in r.text
        assert "思路" in r.text
        assert "event: done" in r.text

    def test_generate_agent_stage_events(self, client, monkeypatch):
        """generate 事件时序: meta → agent(generate) → thinking* → token* → done;memory 由 Java 发(避免双发)"""
        monkeypatch.setattr(
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(deltas=[
                _delta(reasoning="先想思路"),
                _delta(content="思路"),
            ]),
        )
        r = client.post("/api/tutoring/generate", json=generate_payload(), headers=_headers())
        events = _parse_sse(r.text)

        def _idx(event, stage=None):
            return next(i for i, (ev, d) in enumerate(events)
                        if ev == event and (stage is None or d.get("stage") == stage))

        meta_idx = _idx("meta")
        generate_idx = _idx("agent", "generate")
        thinking_idx = _idx("thinking")
        done_idx = _idx("done")
        # 类型先行: meta → agent(generate) → thinking → (token*) → done
        assert meta_idx < generate_idx < thinking_idx < done_idx
        # Python 不发 memory(Java 真实落库后发,避免双发)
        assert "memory" not in [d["stage"] for e, d in events if e == "agent"]

    def test_stream_tokens_concatenated(self, client, monkeypatch):
        monkeypatch.setattr(
            "core.tutoring.ark_stream.stream_chat",
            _FakeArkStream(deltas=[_delta(content="先"), _delta(content="设x"), _delta(content="再列方程")]),
        )
        r = client.post("/api/tutoring/generate", json=generate_payload(), headers=_headers())
        contents = []
        for line in r.text.splitlines():
            if line.startswith("data: "):
                data = json.loads(line[len("data: "):])
                if "content" in data:
                    contents.append(data["content"])
        assert "".join(contents) == "先设x再列方程"
