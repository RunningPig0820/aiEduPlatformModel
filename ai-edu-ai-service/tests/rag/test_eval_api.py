"""
任务 6.4 评测 API 测试

覆盖(6.1/6.2/6.3):
- POST /api/rag/eval/run: 触发评测 → 返回 {ok, version, aggregate, report_path}
- GET /api/rag/eval/report: 查询最新报告 + 历史版本列表
- 鉴权: 缺 token → 403 / 错 token → 403(6.3)

Mock 边界 = run_eval.run_evaluation + run_eval._list_reports(避免真实评测/COU/LLM);
query 端点走真实逻辑(已有 test_rag_query 覆盖)。
"""
import sys
import os
import json

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config.settings import settings

TOKEN = settings.INTERNAL_TOKEN
AUTH = {"x-internal-token": TOKEN}

AGG = {"count": 5, "hit_at_k_avg": 0.8, "quality_avg": 3.6, "judged_ratio": 1.0,
       "avg_latency_ms": 5707, "total_cost_yuan": 0.0803, "avg_cost_yuan": 0.0161,
       "avg_tokens": 4686, "hit_cases": 5, "unjudged": 0}


@pytest.fixture
def client(tmp_path, monkeypatch):
    from api.rag import EVAL_ROUTER
    app = FastAPI()
    app.include_router(EVAL_ROUTER)
    c = TestClient(app)

    # mock run_eval 模块(避免真实评测)—— api/rag.py 函数内 `from scripts.rag import run_eval`
    # 会查 sys.modules, 替换它即可让端点用 fake
    import types
    fake = types.SimpleNamespace(
        REPORT_DIR=str(tmp_path),
        run_evaluation=lambda: {"version": "2026-08-24-test", "aggregate": AGG,
                                "report_path": str(tmp_path / "2026-08-24-test.json"),
                                "trace_path": str(tmp_path / "trace.jsonl"),
                                "results": []},
    )
    fake._list_reports = lambda: []  # report 测试里再覆写
    monkeypatch.setitem(sys.modules, "scripts.rag.run_eval", fake)
    return c


class TestEvalRun:
    """6.1 触发评测"""

    def test_run_ok(self, client):
        r = client.post("/api/rag/eval/run", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["version"] == "2026-08-24-test"
        assert body["aggregate"]["hit_at_k_avg"] == 0.8
        assert body["report_path"]

    def test_run_missing_token_403(self, client):
        assert client.post("/api/rag/eval/run").status_code == 403

    def test_run_wrong_token_403(self, client):
        r = client.post("/api/rag/eval/run", headers={"x-internal-token": "wrong"})
        assert r.status_code == 403


class TestEvalReport:
    """6.2 查询报告"""

    def test_report_ok_has_reports(self, client, tmp_path, monkeypatch):
        # 预置一份历史报告
        os.makedirs(tmp_path, exist_ok=True)
        with open(tmp_path / "2026-08-24-v1.json", "w", encoding="utf-8") as f:
            json.dump({"version": "2026-08-24-v1", "aggregate": AGG}, f, ensure_ascii=False)
        fake = sys.modules["scripts.rag.run_eval"]
        fake._list_reports = lambda: ["2026-08-24-v1.json"]

        r = client.get("/api/rag/eval/report", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["has_report"] is True
        assert body["version"] == "2026-08-24-v1"
        assert body["reports"] == ["2026-08-24-v1.json"]
        assert body["aggregate"]["hit_at_k_avg"] == 0.8

    def test_report_no_history(self, client):
        # fake._list_reports 默认返回 [] → has_report False
        r = client.get("/api/rag/eval/report", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True and body["has_report"] is False
        assert body["reports"] == []

    def test_report_missing_token_403(self, client):
        assert client.get("/api/rag/eval/report").status_code == 403
