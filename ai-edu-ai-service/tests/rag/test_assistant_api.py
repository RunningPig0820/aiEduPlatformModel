"""
B 组白盒 API 测试 - assistant.pipeline_events + api/rag_assistant.py 端点

覆盖(tasks E 组"SSE 事件时序测试" + B 组):
- pipeline_events 事件时序(冻结, 无 permission): intent→(clarify|switch)→rewrite→rerank
  →(boundary|token)→done
  - 正常流: intent→rewrite→rerank→token→done(含 quoted_keys/tokens_usage/suggestions/trace_id)
  - clarify 分支: intent→clarify→done(0 token, 无 rewrite/rerank/token, 短路不调 recall)
  - switch 分支: intent→switch→rewrite(新锚点)→rerank→token→done
  - boundary 分支: intent→rewrite→rerank→boundary→done(**短路纪律: 不调 generate**, 0 token)
  - 生成降级: stream error → done.reason=timeout, suggestions 空
  - 断连中止: generate 前 is_disconnected → 无 token/done
- assemble_usage: tokens_usage 组装(prompt/completion/cache_hit/total)
- guide: 静态池 RAG 定向结构
- API 端点(TestClient, mock pipeline_events / run_eval):
  - POST ask SSE 流式(事件行 + done 回显 trace_id)
  - POST ask 非流式(done + stages 摘要)
  - GET guide / GET eval/report(映射 + 无报告 404)
  - 鉴权 403(缺/错 token)

Mock 边界: pipeline_events 内部单元 mock(不碰真实 doubao/COS); API 层 mock pipeline_events。
"""
import asyncio
import json
import os
import sys
import types

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from config.settings import settings
from core.rag import assistant

TOKEN = settings.INTERNAL_TOKEN
AUTH = {"x-internal-token": TOKEN}

# ---- 引擎层 fake 构造 ----

HIT = {"key": "ai-tutoring/04-安全与防作弊#0", "score": 0.9, "authority": 1.0,
       "source": "完善文档", "file": "04-安全与防作弊", "file_path": "4.完善文档/04-安全与防作弊.md",
       "anchor": "04-安全与防作弊", "summary": "防作弊答案出口机制",
       "text": "防套答案: 第1次要答案拦下给思路"}
RERANK_BLOCK = {"block_id": HIT["key"], "title": HIT["anchor"], "summary": HIT["summary"],
                "file_path": HIT["file_path"], "score": 0.03}


def _intent(**over):
    base = {"anchor": "ai-tutoring", "category": "项目介绍", "switch_detected": False,
            "ambiguous": False, "candidates": [], "locked_sections": ["01", "02"],
            "degraded": False}
    base.update(over)
    return base


def _recall(**over):
    base = {"vec": {"hits": ["v"], "confidence": 0.9},
            "bm25": {"hits": ["b"], "confidence": 0.8},
            "degraded": [],
            "rerank": [RERANK_BLOCK],
            "hits": [HIT],
            "corpus": "ai-tutoring"}
    base.update(over)
    return base


def _patch_base(monkeypatch, intent=None, rewrite=None, recall=None,
                suggestions=None, stream_evs=None):
    """mock 引擎基础单元; 返回供断言的容器。"""
    captured = {"rewrite_anchors": []}
    if intent is None:
        intent = lambda q, h=None, cp="ai-tutoring": _intent()  # noqa: E731
    monkeypatch.setattr(assistant.rag_core, "intent", intent)
    if rewrite is None:
        def _rw(q, a, h=None):
            captured["rewrite_anchors"].append(a)
            return "怎么防学生套答案？"
        rewrite = _rw
    monkeypatch.setattr(assistant.rag_core, "rewrite_query", rewrite)
    if recall is None:
        async def _rec(q, anchor=None, blocks=None, top_k=3):
            return _recall()
        recall = _rec
    monkeypatch.setattr(assistant, "recall", recall)
    if suggestions is not None:
        monkeypatch.setattr(assistant, "gen_suggestions", suggestions)
    if stream_evs is not None:
        _patch_stream(monkeypatch, stream_evs)
    return captured


def _patch_stream(monkeypatch, evs):
    async def _fake(hits, question, request=None, streamer=None):
        for ev in evs:
            yield ev
    monkeypatch.setattr(assistant, "stream_generate", _fake)


def _forbidden_async(*a, **k):
    async def _f(*a2, **k2):
        raise AssertionError("不应被调用")
    return _f


def _collect(agen):
    async def _run():
        return [ev async for ev in agen]
    return asyncio.run(_run())


# ============ 引擎层: pipeline_events 事件时序 ============


class TestPipelineEvents:
    def test_normal_flow(self, monkeypatch):
        """正常流: intent→rewrite→rerank→token→done(quoted/usage/suggestions/trace_id)"""
        cap = _patch_base(monkeypatch, stream_evs=[
            {"type": "token", "text": "防套答案: 第1次要答案拦下给思路"},
            {"type": "usage", "usage": {"prompt_tokens": 320, "completion_tokens": 140}},
        ])
        monkeypatch.setattr(assistant, "gen_suggestions",
                            lambda a, anchor="": ["想了解RAG的整体架构吗？"])
        evs = _collect(assistant.pipeline_events(
            "怎么防学生套答案？", history=[], current_project="ai-tutoring", trace_id="trc-1"))
        assert [e["event"] for e in evs] == ["intent", "rewrite", "rerank", "token", "done"]

        # intent 事件字段齐备
        intent_data = evs[0]["data"]
        assert set(("anchor", "category", "switch_detected", "ambiguous",
                    "candidates", "locked_sections", "degraded")) <= set(intent_data)
        assert intent_data["anchor"] == "ai-tutoring"
        # rewrite 事件(original + rewritten)
        assert evs[1]["data"]["original_question"] == "怎么防学生套答案？"
        assert evs[1]["data"]["rewritten_query"] == "怎么防学生套答案？"
        # rerank 前端契约
        assert evs[2]["data"]["blocks"][0]["block_id"] == HIT["key"]
        # token 增量
        assert evs[3]["data"] == {"text": "防套答案: 第1次要答案拦下给思路"}
        # done: answer 全文 + quoted(LCS 真实命中) + usage 组装 + suggestions + trace_id
        done = evs[4]["data"]
        assert done["answer"] == "防套答案: 第1次要答案拦下给思路"
        assert done["quoted_keys"] == ["ai-tutoring/04-安全与防作弊#0"]
        assert done["tokens_usage"] == {"prompt_tokens": 320, "completion_tokens": 140,
                                        "cache_hit_tokens": 0, "total_tokens": 460}
        assert done["suggestions"] == ["想了解RAG的整体架构吗？"]
        assert done["trace_id"] == "trc-1"
        assert done["reason"] is None

    def test_clarify_short_circuit(self, monkeypatch):
        """ambiguous & 候选≥2 → intent→clarify→done(0 token, 短路不调 recall)"""
        monkeypatch.setattr(
            assistant.rag_core, "intent",
            lambda q, h=None, cp="ai-tutoring":
            _intent(ambiguous=True, candidates=["ai-tutoring", "rag-project"]))
        monkeypatch.setattr(assistant, "recall", _forbidden_async())  # clarify 后不得进 recall
        evs = _collect(assistant.pipeline_events(
            "这个功能的流转", history=[], current_project="rag-project", trace_id="t2"))
        assert [e["event"] for e in evs] == ["intent", "clarify", "done"]
        clarify = evs[1]["data"]
        assert clarify["candidates"] == ["ai-tutoring", "rag-project"]
        assert clarify["default"] == "rag-project"  # current_project 优先
        done = evs[2]["data"]
        assert done["answer"] == ""
        assert done["tokens_usage"]["total_tokens"] == 0
        assert done["reason"] is None
        assert done["trace_id"] == "t2"

    def test_switch_uses_new_anchor(self, monkeypatch):
        """switch_detected → intent→switch→rewrite(新锚点)→rerank→token→done"""
        def _it(q, h=None, cp="ai-tutoring"):
            return _intent(anchor="rag-project", switch_detected=True)
        cap = _patch_base(monkeypatch, intent=_it,
                          stream_evs=[{"type": "token", "text": "RAG 架构"}])
        monkeypatch.setattr(assistant, "gen_suggestions", lambda a, anchor="": [])
        evs = _collect(assistant.pipeline_events(
            "RAG 怎么做的", history=[{"question": "a", "answer": "b", "anchor": "ai-tutoring"}],
            current_project="ai-tutoring", trace_id="t3"))
        assert [e["event"] for e in evs] == ["intent", "switch", "rewrite", "rerank", "token", "done"]
        sw = evs[1]["data"]
        assert sw == {"from_anchor": "ai-tutoring", "to_anchor": "rag-project"}  # from=history 末轮锚点
        assert cap["rewrite_anchors"] == ["rag-project"]  # rewrite 用 to_anchor 走新锚点链路

    def test_boundary_short_circuit_no_generate(self, monkeypatch):
        """边界低置信(空 rerank) → intent→rewrite→rerank→boundary→done, 短路不调 generate"""
        async def _rec(q, anchor=None, blocks=None, top_k=3):
            return _recall(rerank=[], hits=[], vec={"hits": [], "confidence": 0.1},
                           bm25={"hits": [], "confidence": 0.1},
                           degraded=["vector_timeout", "bm25_empty"])

        _patch_base(monkeypatch, recall=_rec)
        monkeypatch.setattr(assistant, "stream_generate", _forbidden_async())  # 短路纪律
        evs = _collect(assistant.pipeline_events("知识图谱怎么用", trace_id="t4"))
        assert [e["event"] for e in evs] == ["intent", "rewrite", "rerank", "boundary", "done"]
        assert evs[3]["data"]["reason"] == "low_confidence"
        done = evs[4]["data"]
        assert done["answer"] == "未找到关联文档，我尚未掌握。"
        assert done["reason"] == "low_confidence"
        assert done["tokens_usage"]["total_tokens"] == 0

    def test_gen_degrade_reason_timeout(self, monkeypatch):
        """生成降级(error 事件) → done.reason=timeout, suggestions 空"""
        _patch_base(monkeypatch, stream_evs=[
            {"type": "error", "text": "生成服务异常，未能生成完整答案。以下为检索到的参考资料："}])
        evs = _collect(assistant.pipeline_events("问题", trace_id="t5"))
        events = [e["event"] for e in evs]
        assert events[-1] == "done"
        done = evs[-1]["data"]
        assert done["reason"] == "timeout"
        assert done["suggestions"] == []          # 降级不生成引导
        assert "生成服务异常" in done["answer"]

    def test_disconnect_aborts_before_generate(self, monkeypatch):
        """generate 前 is_disconnected → 中止(无 token/done)"""
        _patch_base(monkeypatch)

        class _Req:
            def __init__(self):
                self.calls = 0

            async def is_disconnected(self):
                self.calls += 1
                return True  # 首次即断(recall 完成、generate 前)

        evs = _collect(assistant.pipeline_events("问题", request=_Req()))
        assert [e["event"] for e in evs] == ["intent", "rewrite", "rerank"]  # 无 token/done

    def test_history_passed_to_intent(self, monkeypatch):
        """history 传给 intent 消费(只读透传; 截断在 query.intent 内部, A1 已测 _truncate_history)"""
        seen = {}

        def _it(q, h=None, cp="ai-tutoring"):
            seen["hist_len"] = len(h or [])
            return _intent()

        _patch_base(monkeypatch, intent=_it,
                    stream_evs=[{"type": "token", "text": "答案"}])
        monkeypatch.setattr(assistant, "gen_suggestions", lambda a, anchor="": [])
        hist = [{"question": f"q{i}", "answer": "a", "anchor": "ai-tutoring"} for i in range(5)]
        _collect(assistant.pipeline_events("问题", history=hist, trace_id="t6"))
        # pipeline 透传完整 history(Java 传最近 N 轮); 真实 intent 内部 _truncate_history(3) 截断
        assert seen["hist_len"] == 5


# ============ assemble_usage / guide ============


class TestAssembleUsage:
    def test_none_all_zero(self):
        assert assistant.assemble_usage(None) == {
            "prompt_tokens": 0, "completion_tokens": 0,
            "cache_hit_tokens": 0, "total_tokens": 0}

    def test_plain_usage(self):
        u = assistant.assemble_usage({"prompt_tokens": 320, "completion_tokens": 140})
        assert u["prompt_tokens"] == 320 and u["completion_tokens"] == 140
        assert u["cache_hit_tokens"] == 0 and u["total_tokens"] == 460

    def test_cached_tokens(self):
        u = assistant.assemble_usage({
            "prompt_tokens": 320, "completion_tokens": 140,
            "prompt_tokens_details": {"cached_tokens": 200}})
        assert u["cache_hit_tokens"] == 200
        assert u["total_tokens"] == 460

    def test_missing_fields_guard(self):
        """缺字段不崩(取 0)"""
        u = assistant.assemble_usage({"completion_tokens": 5})
        assert u["prompt_tokens"] == 0 and u["total_tokens"] == 5


class TestGuide:
    def test_guide_static_pool(self):
        data = assistant.guide()
        sugs = data["suggestions"]
        assert 1 <= len(sugs) <= 3
        assert all("title" in s and "direction" in s for s in sugs)
        assert all(s["direction"] in ("architecture", "data_flow", "evaluation")
                   for s in sugs)
        # RAG 定向: 方向闭集均为 RAG 项目主题 + 至少一条 title 含字面 RAG
        assert any("RAG" in s["title"] for s in sugs)


# ============ API 层端点(TestClient) ============


def _fake_pipeline(evs):
    async def _f(question, history=None, current_project="ai-tutoring", trace_id="",
                 top_k=3, request=None, blocks=None):
        for ev in evs:
            yield ev
    return _f


@pytest.fixture
def client(tmp_path, monkeypatch):
    from api.rag_assistant import router
    app = FastAPI()
    app.include_router(router)
    c = TestClient(app)
    # mock run_eval(仅 eval/report 用; 同 test_eval_api.py 的 sys.modules 手法)
    fake = types.SimpleNamespace(REPORT_DIR=str(tmp_path))
    fake._list_reports = lambda: []
    monkeypatch.setitem(sys.modules, "scripts.rag.run_eval", fake)
    return c


DONE = {"answer": "答案", "quoted_keys": [], "trace_id": "trc-xyz",
        "tokens_usage": {"prompt_tokens": 320, "completion_tokens": 140,
                         "cache_hit_tokens": 0, "total_tokens": 460},
        "suggestions": ["想了解RAG的整体架构吗？"], "reason": None}


class TestAskSSE:
    def test_sse_event_sequence(self, client, monkeypatch):
        """SSE 事件行按序输出 + done 回显 trace_id"""
        evs = [
            {"event": "intent", "data": {"anchor": "ai-tutoring", "category": "项目介绍",
                                         "switch_detected": False, "ambiguous": False,
                                         "candidates": [], "locked_sections": ["01"], "degraded": False}},
            {"event": "rewrite", "data": {"original_question": "q", "rewritten_query": "q改写"}},
            {"event": "rerank", "data": {"blocks": [{"block_id": "b1", "title": "t", "summary": "s",
                                                     "file_path": "f", "score": 0.9}]}},
            {"event": "token", "data": {"text": "答案"}},
            {"event": "done", "data": DONE},
        ]
        monkeypatch.setattr(assistant, "pipeline_events", _fake_pipeline(evs))
        r = client.post("/api/rag/assistant/ask", headers=AUTH,
                        json={"question": "q", "stream": True, "trace_id": "trc-xyz"})
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        body = r.text
        # 事件顺序(按 text 出现次序)
        idx = [body.find(f"event: {e}") for e in ("intent", "rewrite", "rerank", "token", "done")]
        assert all(i >= 0 for i in idx) and idx == sorted(idx)
        assert '"trace_id": "trc-xyz"' in body  # done 回显 trace_id

    def test_sse_missing_token_403(self, client):
        assert client.post("/api/rag/assistant/ask",
                           json={"question": "q", "stream": True}).status_code == 403

    def test_sse_wrong_token_403(self, client):
        assert client.post("/api/rag/assistant/ask",
                           headers={"x-internal-token": "bad"},
                           json={"question": "q", "stream": True}).status_code == 403


class TestAskNonStream:
    def test_done_with_stages(self, client, monkeypatch):
        """非流式: done 数据 + stages 摘要(intent/rewrite/rerank)"""
        evs = [
            {"event": "intent", "data": {"anchor": "ai-tutoring", "category": "项目介绍",
                                         "switch_detected": False, "ambiguous": False,
                                         "candidates": [], "locked_sections": ["01"], "degraded": False}},
            {"event": "rewrite", "data": {"original_question": "原问", "rewritten_query": "改写问"}},
            {"event": "rerank", "data": {"blocks": [{"block_id": "b1", "title": "t", "summary": "s",
                                                     "file_path": "f", "score": 0.9}]}},
            {"event": "done", "data": DONE},
        ]
        monkeypatch.setattr(assistant, "pipeline_events", _fake_pipeline(evs))
        r = client.post("/api/rag/assistant/ask", headers=AUTH, json={"question": "q"})
        assert r.status_code == 200
        body = r.json()
        assert body["answer"] == "答案"
        assert body["trace_id"] == "trc-xyz"
        assert body["reason"] is None
        assert body["stages"]["intent"]["anchor"] == "ai-tutoring"
        assert body["stages"]["rewrite"] == {"original_question": "原问",
                                             "rewritten_query": "改写问"}
        assert body["stages"]["rerank"][0]["block_id"] == "b1"

    def test_question_required_422(self, client):
        assert client.post("/api/rag/assistant/ask", headers=AUTH, json={}).status_code == 422

    def test_top_k_range_422(self, client):
        assert client.post("/api/rag/assistant/ask", headers=AUTH,
                           json={"question": "q", "top_k": 9}).status_code == 422

    def test_missing_token_403(self, client):
        assert client.post("/api/rag/assistant/ask", json={"question": "q"}).status_code == 403


class TestGuideAPI:
    def test_guide(self, client):
        r = client.get("/api/rag/assistant/guide", headers=AUTH)
        assert r.status_code == 200
        sugs = r.json()["suggestions"]
        assert 1 <= len(sugs) <= 3
        assert all("title" in s and "direction" in s for s in sugs)

    def test_guide_missing_token_403(self, client):
        assert client.get("/api/rag/assistant/guide").status_code == 403


class TestEvalReportAPI:
    def test_report_mapping(self, client, tmp_path):
        """baseline 报告字段映射(version/count/hit_at_3/quality_avg/latency/cost/judged)"""
        with open(tmp_path / "2026-08-25-abcd123.json", "w", encoding="utf-8") as f:
            json.dump({"version": "2026-08-25-abcd123", "aggregate": {
                "count": 15, "hit_at_k_avg": 0.8, "quality_avg": 4.2,
                "avg_latency_ms": 5599, "avg_cost_yuan": 0.0157, "judged_ratio": 1.0,
                "total_cost_yuan": 0.2355, "avg_tokens": 4686, "hit_cases": 12,
                "unjudged": 0}}, f, ensure_ascii=False)
        sys.modules["scripts.rag.run_eval"]._list_reports = \
            lambda: ["2026-08-25-abcd123.json"]
        r = client.get("/api/rag/assistant/eval/report", headers=AUTH)
        assert r.status_code == 200
        body = r.json()
        assert body["version"] == "2026-08-25-abcd123"
        assert body["count"] == 15
        assert body["hit_at_3"] == 0.8
        assert body["quality_avg"] == 4.2
        assert body["avg_latency_ms"] == 5599
        assert body["avg_cost_yuan"] == 0.0157
        assert body["judged_ratio"] == 1.0

    def test_report_no_report_404(self, client):
        """无报告 → 404(暂无评估报告)"""
        r = client.get("/api/rag/assistant/eval/report", headers=AUTH)
        assert r.status_code == 404
        assert "暂无评估报告" in r.json()["detail"]

    def test_report_missing_token_403(self, client):
        assert client.get("/api/rag/assistant/eval/report").status_code == 403
