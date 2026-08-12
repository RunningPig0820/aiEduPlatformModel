"""
任务 5.3: agent 事件流 real 冒烟(需要 DOUBAO_API_KEY,无 key 自动 skip)

真实 doubao + 真实题图:
- decide 流式: agent(perceive→analyze→plan→decide) + meta(ActionMeta) + done
- generate 流式: agent(generate) + token* + agent(memory) + done
"""
import json

import pytest
from fastapi.testclient import TestClient

TEST_IMAGE_URL = "https://ai-edu-1318177119.cos.ap-guangzhou.myqcloud.com/tutoring-test/images/math.png"


def _parse_sse(text):
    """解析 SSE 文本为 [(event, data_dict), ...]"""
    events = []
    for block in text.split("\n\n"):
        event = data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: "):]
            elif line.startswith("data: "):
                data = json.loads(line[len("data: "):])
        if event:
            events.append((event, data))
    return events


@pytest.mark.requires_doubao
class TestAgentFlowReal:
    """agent 事件流 real 冒烟"""

    def _client_headers(self):
        from main import app
        from config.settings import settings

        return TestClient(app), {"x-internal-token": settings.INTERNAL_TOKEN}

    def test_decide_stream_full(self):
        """decide 流式: agent 阶段序列 + meta(ActionMeta) + done"""
        client, h = self._client_headers()
        r = client.post("/api/tutoring/decide", json={
            "history": [
                {"role": "user", "content": "", "image_url": TEST_IMAGE_URL},
                {"role": "user", "content": "老师这题怎么做?"},
            ],
            "round_count": 1,
            "answer_request_count": 0,
            "mastery_snapshot": [],
            "subject_hint": "math",
        }, headers=h)

        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        events = _parse_sse(r.text)
        # agent 阶段序列(前 4 个)
        stages = [d["stage"] for e, d in events if e == "agent"]
        assert stages[:4] == ["perceive", "analyze", "plan", "decide"]
        # meta 携带合法 ActionMeta(闭集)
        meta = next(d for e, d in events if e == "meta")
        assert meta["type"] in {"hint", "approach", "reveal", "concept", "switch", "end"}
        # done 收尾
        assert events[-1][0] == "done"

    def test_generate_stream_full(self):
        """generate 流式: agent(generate) + token* + agent(memory) + done"""
        client, h = self._client_headers()
        r = client.post("/api/tutoring/generate", json={
            "history": [
                {"role": "user", "content": "", "image_url": TEST_IMAGE_URL},
                {"role": "user", "content": "老师这题怎么做?"},
            ],
            "subject_hint": "math",
            "action_type": "hint",
        }, headers=h)

        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        events = _parse_sse(r.text)
        stages = [d["stage"] for e, d in events if e == "agent"]
        assert "generate" in stages
        tokens = [d["content"] for e, d in events if e == "token"]
        assert tokens  # 有引导内容
        assert events[-1][0] == "done"
