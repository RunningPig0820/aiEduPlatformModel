"""
任务 3.5/3.6 评测 agent 测试

覆盖:
- 3.2 hit@k 计算(纯函数): 命中/部分命中/未命中/空引用/k 边界
- 3.3 LLM 判分: 正常解析 / JSON 解析失败重试1次记0 / score 越界重试
- 3.1 单条评测: mock 检索+生成+判分 → 输出齐全(question/recall/hit/answer/score/latency)
- 3.4 聚合: 模块指标正确(hit@k 均值/质量分均值/judged 比例)

Mock 边界 = retrieve_vector/generate/judge_quality/_load_blocks(不碰真实 COS/LLM);
orchestrate/hit_at_k/aggregate 纯逻辑离线可测。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

from core.rag import eval_agent
from core.rag import query as rag_core

# 测试语料块(与 test_rag_query 同构: 完善文档 04 权威1.0 + 语雀 01 0.7)
BLOCKS = [
    {"text": "防套答案: 第1次要答案拦下给思路, count+1; 第2次才放行完整答案",
     "summary": "防作弊答案出口机制",
     "tags": {"module": "ai-tutoring", "section": "04", "source": "完善文档",
              "authority": 1.0, "file": "04-安全与防作弊", "file_path": "4.完善文档/04-安全与防作弊.md",
              "anchor": "04-安全与防作弊"}},
    {"text": "AI答疑面向小学到高中全学段, 启发式教学, 不直接给答案",
     "summary": "AI答疑定位与理念",
     "tags": {"module": "ai-tutoring", "section": "01", "source": "语雀",
              "authority": 0.7, "file": "语雀-答疑理念", "file_path": "1.语雀/答疑理念.md",
              "anchor": "答疑理念"}},
]

CASE = {
    "module": "ai-tutoring", "question": "怎么防学生套答案？", "question_type": "难点",
    "expected_references": ["ai-tutoring/04-安全与防作弊（护栏）"],
    "expected_points": ["reveal 两次出口", "count 计数", "Java 硬拦"],
}


class TestHitAtK:
    """3.2 hit@k 纯函数"""

    def _recall(self, sections):
        return [{"section": s, "key": f"ai-tutoring/{s}", "score": 1.0 - i * 0.1,
                 "authority": 1.0, "file": s, "anchor": s} for i, s in enumerate(sections)]

    def test_hit_top1(self):
        r = self._recall(["04", "07", "02"])
        assert eval_agent.hit_at_k(r, ["ai-tutoring/04-安全与防作弊"]) == 1.0

    def test_partial_hit(self):
        # 预期 04+07, 召回 top3 只有 04 → 0.5
        r = self._recall(["04", "02", "06"])
        assert eval_agent.hit_at_k(r, ["ai-tutoring/04-安全", "ai-tutoring/07-流式"]) == 0.5

    def test_miss(self):
        r = self._recall(["01", "02", "06"])
        assert eval_agent.hit_at_k(r, ["ai-tutoring/04-安全"]) == 0.0

    def test_respects_k(self):
        # 预期节在 top4, k=3 → 未命中
        r = self._recall(["01", "02", "06", "04"])
        assert eval_agent.hit_at_k(r, ["ai-tutoring/04-安全"], k=3) == 0.0
        assert eval_agent.hit_at_k(r, ["ai-tutoring/04-安全"], k=4) == 1.0

    def test_empty_expected(self):
        assert eval_agent.hit_at_k(self._recall(["04"]), []) == 0.0

    def test_auto_fill_k(self):
        r = self._recall(["04", "02", "06"])
        assert eval_agent.hit_at_k(r, ["ai-tutoring/04-安全"]) == 1.0  # 默认 k=HIT_K


class FakeLLM:
    """假判分 LLM: 可配置返回内容或抛异常"""

    def __init__(self, text=None, exc=None):
        self.text = text
        self.exc = exc
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        if self.exc:
            raise self.exc
        return type("R", (), {"content": self.text})()


class TestJudgeQuality:
    """3.3 LLM 判分"""

    def test_judge_ok(self):
        llm = FakeLLM('{"score": 4, "rationale": "覆盖大部分要点"}')
        r = eval_agent.judge_quality("q", "a", ["p1"], llm=llm)
        assert r == {"score": 4, "rationale": "覆盖大部分要点", "judged": True}

    def test_judge_score_out_of_range_retries(self):
        # 第一次越界(score=9), 第二次正常 → 返回正常
        llm = FakeLLM(text='{"score": 4, "rationale": "ok"}')
        # 让第一次输出越界: 用计数控制
        orig_extract = eval_agent._extract_json
        call_count = [0]

        def flaky(text):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"score": 9, "rationale": "bad"}
            return {"score": 4, "rationale": "ok"}

        eval_agent._extract_json = flaky
        try:
            r = eval_agent.judge_quality("q", "a", ["p"], llm=llm)
            assert r["score"] == 4 and r["judged"]
        finally:
            eval_agent._extract_json = orig_extract

    def test_judge_parse_fail_marks_0(self):
        # 两次都解析失败 → score 0, judged False
        llm = FakeLLM(text="不是 JSON")
        r = eval_agent.judge_quality("q", "a", ["p"], llm=llm)
        assert r["score"] == 0 and r["judged"] is False

    def test_judge_llm_exception_marks_0(self):
        llm = FakeLLM(exc=RuntimeError("down"))
        r = eval_agent.judge_quality("q", "a", ["p"], llm=llm)
        assert r["score"] == 0 and r["judged"] is False


class TestRunEvalCase:
    """3.1 单条评测执行(全 mock 外部边界)"""

    @pytest.fixture
    def mock_core(self, monkeypatch):
        monkeypatch.setattr(rag_core, "_load_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "_llm_category", lambda q: "难点")  # classify 内部用
        # 向量路返回 04 块(命中 expected_references)
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0",
                                                  "distance": 0.1}], "confidence": 0.9})
        # 生成 mock 掉(doubao 不碰); 判分 mock 掉
        monkeypatch.setattr(rag_core, "generate", lambda hits, q: "mock 答案")
        monkeypatch.setattr(eval_agent, "judge_quality",
                            lambda q, a, pts, corpus_texts=None: {"score": 4, "rationale": "ok", "judged": True})

    def test_case_output_complete(self, mock_core):
        trace = eval_agent.run_eval_case(CASE)
        # 输出齐全(3.5: question/recall/hit/answer/score/latency)
        for field in ("question", "question_type", "intent", "recall", "hit",
                      "hit_score", "answer", "references", "score", "rationale",
                      "judged", "latency_ms", "version"):
            assert field in trace, f"缺字段 {field}"
        assert trace["question"] == CASE["question"]
        assert trace["hit"] is True          # 04 命中
        assert trace["score"] == 4
        assert trace["recall"] and trace["recall"][0]["section"] == "04"
        assert set(trace["latency_ms"]) == {"retrieve_ms", "generate_ms", "total_ms"}

    def test_case_vector_retrieve_called(self, mock_core, monkeypatch):
        # 评测走真实 retrieve_vector(不降级)—— 验证被调用(而非跳过)
        called = []
        real = rag_core.retrieve_vector
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: (called.append(q), real(q))[1])
        eval_agent.run_eval_case(CASE)
        assert called, "评测应走真实 retrieve_vector(不降级)"


class TestAggregate:
    """3.4 聚合"""

    def _trace(self, hit_score, score, judged=True, total_ms=100):
        return {"hit_score": hit_score, "score": score, "judged": judged,
                "hit": hit_score > 0, "latency_ms": {"total_ms": total_ms}}

    def test_aggregate_empty(self):
        a = eval_agent.aggregate([])
        assert a["count"] == 0

    def test_aggregate_metrics(self):
        results = [
            self._trace(1.0, 4, True, 100),
            self._trace(0.5, 3, True, 200),
            self._trace(0.0, 0, False, 300),
        ]
        a = eval_agent.aggregate(results)
        assert a["count"] == 3
        assert a["hit_at_k_avg"] == round((1.0 + 0.5 + 0.0) / 3, 3)   # 0.5
        assert a["quality_avg"] == round((4 + 3 + 0) / 3, 3)          # 2.333
        assert a["judged_ratio"] == round(2 / 3, 3)                   # 0.667
        assert a["avg_latency_ms"] == 200
        assert a["hit_cases"] == 2
        assert a["unjudged"] == 1
