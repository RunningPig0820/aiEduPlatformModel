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


class TestScoreFromCovered:
    """_score_from_covered 纯函数: 覆盖比例 + 编造封顶硬算"""

    def test_full_cover_no_fab(self):
        assert eval_agent._score_from_covered(5, 5, False) == 5
        assert eval_agent._score_from_covered(4, 5, False) == 4   # 80%
        assert eval_agent._score_from_covered(3, 5, False) == 3   # 60%
        assert eval_agent._score_from_covered(2, 5, False) == 2   # 40%
        assert eval_agent._score_from_covered(1, 5, False) == 1   # 20%
        assert eval_agent._score_from_covered(0, 5, False) == 0

    def test_fabricated_caps_at_3(self):
        """编造封顶 3 分: 覆盖全对但编造 → 3; 覆盖少+编造 → 1~2"""
        assert eval_agent._score_from_covered(5, 5, True) == 3    # 全覆盖也封顶
        assert eval_agent._score_from_covered(4, 5, True) == 3
        assert eval_agent._score_from_covered(2, 5, True) == 2    # 覆盖少 + 编造 → min(2,3)
        assert eval_agent._score_from_covered(1, 5, True) == 1
        assert eval_agent._score_from_covered(0, 5, True) == 0


class TestJudgeQuality:
    """3.3 LLM 判分(模型报 covered_count/fabricated, 代码算分)"""

    def test_judge_ok(self):
        # 覆盖 4/5, 无编造 → 4 分
        llm = FakeLLM('{"covered_count": 4, "fabricated": false, "rationale": "覆盖4/5"}')
        r = eval_agent.judge_quality("q", "a", ["p"] * 5, llm=llm)
        assert r["score"] == 4 and r["judged"] and r["rationale"] == "覆盖4/5"

    def test_judge_full_cover_no_fab_5(self):
        llm = FakeLLM('{"covered_count": 5, "fabricated": false, "rationale": "全覆盖"}')
        assert eval_agent.judge_quality("q", "a", ["p"] * 5, llm=llm)["score"] == 5

    def test_judge_fabricated_caps(self):
        # 覆盖 5/5 但编造 → 封顶 3
        llm = FakeLLM('{"covered_count": 5, "fabricated": true, "rationale": "全覆盖但编造"}')
        assert eval_agent.judge_quality("q", "a", ["p"] * 5, llm=llm)["score"] == 3

    def test_judge_count_out_of_range_retries(self):
        # 第一次越界(covered_count=9), 第二次正常 → 返回正常
        llm = FakeLLM(text='{"covered_count": 4, "fabricated": false, "rationale": "ok"}')
        orig_extract = eval_agent._extract_json
        call_count = [0]

        def flaky(text):
            call_count[0] += 1
            if call_count[0] == 1:
                return {"covered_count": 9, "fabricated": False, "rationale": "bad"}
            return {"covered_count": 4, "fabricated": False, "rationale": "ok"}

        eval_agent._extract_json = flaky
        try:
            r = eval_agent.judge_quality("q", "a", ["p"] * 5, llm=llm)
            assert r["score"] == 4 and r["judged"]
        finally:
            eval_agent._extract_json = orig_extract

    def test_judge_parse_fail_marks_0(self):
        # 两次都解析失败 → score 0, judged False
        llm = FakeLLM(text="不是 JSON")
        r = eval_agent.judge_quality("q", "a", ["p"] * 5, llm=llm)
        assert r["score"] == 0 and r["judged"] is False

    def test_judge_llm_exception_marks_0(self):
        llm = FakeLLM(exc=RuntimeError("down"))
        r = eval_agent.judge_quality("q", "a", ["p"] * 5, llm=llm)
        assert r["score"] == 0 and r["judged"] is False


class TestRunEvalCase:
    """3.1 单条评测执行(全 mock 外部边界)"""

    @pytest.fixture
    def mock_core(self, monkeypatch):
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "_llm_intent",
                            lambda q, h, current_project="ai-tutoring": {
                                "anchor": "ai-tutoring", "category": "难点", "categories": ["开发难点"],
                                "switch_detected": False, "ambiguous": False, "candidates": []})
        # 双池召回: 全量池返回 04 块(命中 expected_references)
        monkeypatch.setattr(rag_core, "retrieve_dual",
                            lambda q, corpus=None, locked_categories=None: {
                                "full": {"hits": [{"key": "rag-slice/04-安全与防作弊/04-安全与防作弊#0",
                                                   "distance": 0.1}], "confidence": 0.9},
                                "slice": {"hits": [], "confidence": 0.0},
                                "slice_q": {"hits": [], "confidence": 0.0},   # 双向量: summary/问题路
                                "bm25": {"hits": [], "confidence": 0.0}})
        # 生成 mock 掉(doubao 不碰); 判分 mock 掉
        monkeypatch.setattr(rag_core, "generate",
                            lambda hits, q, return_usage=False:
                                ("mock 答案", {"prompt_tokens": 100, "completion_tokens": 50,
                                               "total_tokens": 150}) if return_usage else "mock 答案")
        monkeypatch.setattr(eval_agent, "judge_quality",
                            lambda q, a, pts, corpus_texts=None: {"score": 4, "rationale": "ok", "judged": True,
                                                                  "usage": {"prompt_tokens": 80, "completion_tokens": 20,
                                                                            "total_tokens": 100}})

    def test_case_output_complete(self, mock_core):
        trace = eval_agent.run_eval_case(CASE)
        # 输出齐全(3.5: question/recall/hit/answer/score/latency; 4: usage)
        for field in ("question", "question_type", "intent", "recall", "hit",
                      "hit_score", "answer", "references", "score", "rationale",
                      "judged", "usage", "latency_ms", "version"):
            assert field in trace, f"缺字段 {field}"
        assert trace["question"] == CASE["question"]
        assert trace["hit"] is True          # 04 命中
        assert trace["score"] == 4
        assert trace["recall"] and trace["recall"][0]["section"] == "04"
        assert set(trace["latency_ms"]) == {"retrieve_ms", "generate_ms", "total_ms"}
        # 4.1 usage: generate(150) + judge(100) = 250 tokens, cost > 0
        assert trace["usage"]["total_tokens"] == 250
        assert trace["usage"]["cost_yuan"] > 0

    def test_case_vector_retrieve_called(self, mock_core, monkeypatch):
        # 评测走真实 retrieve_dual(不降级)—— 验证被调用(而非跳过)
        called = []
        real = rag_core.retrieve_dual
        monkeypatch.setattr(rag_core, "retrieve_dual",
                            lambda q, corpus=None, locked_categories=None:
                                (called.append(q), real(q, corpus=corpus,
                                                        locked_categories=locked_categories))[1])
        eval_agent.run_eval_case(CASE)
        assert called, "评测应走真实 retrieve_dual(不降级)"


class TestPrecisionAtK:
    """D2: precision@k 纯函数(top-k 相关块占比)"""

    def _recall(self, sections):
        return [{"section": s, "key": f"ai-tutoring/{s}", "score": 1.0 - i * 0.1,
                 "authority": 1.0, "file": s, "anchor": s} for i, s in enumerate(sections)]

    def test_all_related(self):
        """3 块全部命中预期来源 → precision@k = 3/HIT_K(默认 k=5)"""
        r = self._recall(["04", "07", "02"])
        assert eval_agent.precision_at_k(
            r, ["ai-tutoring/04-安全", "ai-tutoring/07-流式", "ai-tutoring/02-一次完整答疑"]) == 3 / eval_agent.HIT_K

    def test_two_of_three_again(self):
        """top-k 含 2 个相关块 → precision@k = 2/HIT_K(spec 场景)"""
        r = self._recall(["04", "02", "07"])
        assert eval_agent.precision_at_k(r, ["ai-tutoring/04-安全", "ai-tutoring/07-流式"]) == 2 / eval_agent.HIT_K

    def test_none_related(self):
        r = self._recall(["01", "02", "06"])
        assert eval_agent.precision_at_k(r, ["ai-tutoring/04-安全"]) == 0.0

    def test_respects_k(self):
        """k=3 只看 top3: 相关块在 top4 不计入; k=4 计入(分母固定为 k)"""
        r = self._recall(["04", "01", "02", "06"])
        assert eval_agent.precision_at_k(r, ["ai-tutoring/04-安全"], k=3) == 1 / 3
        assert eval_agent.precision_at_k(r, ["ai-tutoring/04-安全"], k=4) == 1 / 4

    def test_empty_expected(self):
        assert eval_agent.precision_at_k(self._recall(["04"]), []) == 0.0

    def test_auto_fill_k(self):
        r = self._recall(["04", "02", "06"])
        assert eval_agent.precision_at_k(r, ["ai-tutoring/04-安全"]) == 1 / eval_agent.HIT_K  # 默认 k=HIT_K


class TestBoundaryRefusal:
    """D1: 边界拒答类型 —— 断言触发固定话术且 0 token(不进 generate)"""

    @pytest.fixture
    def boundary_case(self):
        return {"module": "ai-tutoring", "question": "帮我写辞职信。",
                "question_type": "边界拒答", "expected_references": [],
                "expected_points": ["应拒答", "不生成答案"]}

    def _mock_low_conf(self, monkeypatch, hits_empty=True):
        """低置信检索: 向量/BM25 双路都低 → 触发 boundary"""
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "_llm_intent",
                            lambda q, h, current_project="ai-tutoring": {
                                "anchor": "ai-tutoring", "category": "难点", "categories": ["开发难点"],
                                "switch_detected": False, "ambiguous": False, "candidates": []})
        monkeypatch.setattr(rag_core, "retrieve_dual",
                            lambda q, corpus=None, locked_categories=None: {
                                "full": {"hits": [], "confidence": 0.1},
                                "slice": {"hits": [], "confidence": 0.1},
                                "slice_q": {"hits": [], "confidence": 0.1},
                                "bm25": {"hits": [], "confidence": 0.1}})
        monkeypatch.setattr(rag_core, "orchestrate", lambda *a, **k: [])
        # 边界拒答不得进 generate/判分(0 token)
        monkeypatch.setattr(rag_core, "generate", _forbidden_generate)
        monkeypatch.setattr(eval_agent, "judge_quality", _forbidden_judge)

    def test_boundary_refusal_ok(self, monkeypatch, boundary_case):
        """低置信 → 拒答正确: 固定话术, score=5, 0 token"""
        self._mock_low_conf(monkeypatch)
        trace = eval_agent.run_eval_case(boundary_case)
        assert trace["question_type"] == "边界拒答"
        assert "未找到关联文档" in trace["answer"]          # 固定话术
        assert trace["score"] == 5                          # 拒答正确满分
        assert trace["usage"]["total_tokens"] == 0          # 0 token
        assert trace["usage"]["cost_yuan"] == 0.0
        assert trace["quoted_valid"] is True
        assert trace["judged"] is True

    def test_boundary_refusal_fail_high_conf(self, monkeypatch, boundary_case):
        """意外高置信命中 → 拒答失败 score=0(语义: 该拒答却答了)"""
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "_llm_intent",
                            lambda q, h, current_project="ai-tutoring": {
                                "anchor": "ai-tutoring", "category": "难点", "categories": ["开发难点"],
                                "switch_detected": False, "ambiguous": False, "candidates": []})
        monkeypatch.setattr(rag_core, "retrieve_dual",
                            lambda q, corpus=None, locked_categories=None: {
                                "full": {"hits": ["v"], "confidence": 0.9},
                                "slice": {"hits": [], "confidence": 0.9},
                                "slice_q": {"hits": [], "confidence": 0.9},
                                "bm25": {"hits": ["b"], "confidence": 0.8}})
        # orchestrate 返回相关块(04)
        monkeypatch.setattr(rag_core, "orchestrate", lambda *a, **k: [{
            "key": "rag-slice/04-安全与防作弊#0", "score": 0.9, "authority": 1.0,
            "section": "04", "file": "04-安全与防作弊", "anchor": "04-安全与防作弊",
            "text": "防套答案", "summary": "s", "file_path": "f"}])
        trace = eval_agent.run_eval_case(boundary_case)
        assert trace["score"] == 0
        assert trace["answer"] == ""                          # 拒答失败, 未产出固定话术
        assert "拒答失败" in trace["rationale"]


def _forbidden_generate(*a, **k):
    raise AssertionError("边界拒答不得进 generate(0 token 断言)")


def _forbidden_judge(*a, **k):
    raise AssertionError("边界拒答不得调 LLM 判分(0 token 断言)")


class TestQuotedCheck:
    """D3: is_quoted 校验 —— quotedKeys ⊆ 召回块 key"""

    def _hits(self, text):
        return [{"key": "ai-tutoring/04-安全与防作弊#0", "text": text,
                 "authority": 1.0, "section": "04", "file": "04-安全与防作弊",
                 "anchor": "04-安全与防作弊"}]

    def test_quoted_keys_subset_of_recall(self):
        """答案引用召回块原文 → quoted_keys ∈ 召回块 key 集合"""
        text = "防套答案: 第1次要答案拦下给思路"
        hits = self._hits(text)
        quoted, valid = eval_agent._quoted_check(text, hits)
        assert quoted == ["ai-tutoring/04-安全与防作弊#0"]
        assert valid is True

    def test_empty_answer_valid(self):
        """空 answer(降级/拒答) → 空 quoted_keys, valid=True"""
        quoted, valid = eval_agent._quoted_check("", self._hits("x"))
        assert quoted == [] and valid is True

    def test_rewritten_answer_not_quoted(self):
        """答案改写未命中原文 → 无引用, 仍合法(不要求必引用)"""
        text = "防套答案: 第1次要答案拦下给思路"
        quoted, valid = eval_agent._quoted_check("完全是另一段话", self._hits(text))
        assert quoted == [] and valid is True

    def test_recall_empty_valid(self):
        """无召回块 → 空引用合法"""
        quoted, valid = eval_agent._quoted_check("防套答案: 第1次要答案拦下给思路", [])
        assert quoted == [] and valid is True


class TestCost:
    """4.1 cost 计算纯函数"""

    def test_calc_cost_known(self):
        # 1000 prompt token × 0.003 + 500 completion × 0.009 = 0.003 + 0.0045 = 0.0075
        assert eval_agent.calc_cost({"prompt_tokens": 1000, "completion_tokens": 500}) == 0.0075

    def test_calc_cost_zero(self):
        assert eval_agent.calc_cost({}) == 0.0
        assert eval_agent.calc_cost({"prompt_tokens": 0, "completion_tokens": 0}) == 0.0

    def test_score_from_covered_full(self):
        assert eval_agent._score_from_covered(5, 5, False) == 5


class TestAggregate:
    """3.4 聚合 + 4.1/4.2 cost/latency"""

    def _trace(self, hit_score, score, judged=True, total_ms=100, cost=0.01, tokens=100):
        return {"hit_score": hit_score, "score": score, "judged": judged,
                "hit": hit_score > 0, "latency_ms": {"total_ms": total_ms},
                "usage": {"cost_yuan": cost, "total_tokens": tokens}}

    def test_aggregate_empty(self):
        a = eval_agent.aggregate([])
        assert a["count"] == 0
        assert a["total_cost_yuan"] == 0.0

    def test_aggregate_metrics(self):
        results = [
            self._trace(1.0, 4, True, 100, 0.01, 100),
            self._trace(0.5, 3, True, 200, 0.02, 200),
            self._trace(0.0, 0, False, 300, 0.03, 300),
        ]
        a = eval_agent.aggregate(results)
        assert a["count"] == 3
        assert a["hit_at_k_avg"] == round((1.0 + 0.5 + 0.0) / 3, 3)   # 0.5
        assert a["quality_avg"] == round((4 + 3 + 0) / 3, 3)          # 2.333
        assert a["judged_ratio"] == round(2 / 3, 3)                   # 0.667
        assert a["avg_latency_ms"] == 200
        assert a["hit_cases"] == 2
        assert a["unjudged"] == 1
        # 4.1/4.2 聚合
        assert a["total_cost_yuan"] == round(0.01 + 0.02 + 0.03, 4)   # 0.06
        assert a["avg_cost_yuan"] == round(0.06 / 3, 4)               # 0.02
        assert a["avg_tokens"] == 200
