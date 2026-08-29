"""
任务 5.4/5.5 可观测评测测试

覆盖:
- 5.1 trace 落盘: JSONL 完整(query/召回/得分/hit/答案/引用/usage/耗时/判分), 可回溯单条
- 5.2 报告生成: 按版本落盘, 含聚合指标 + 语料版本标识
- 5.3 报告版本对比: 新旧两次 hit@k/质量分变化(纯函数 _compare 打印, 验证选对报告)
- 4.3 成本与耗时: calc_cost 纯函数(见 test_eval_agent TestCost)

Mock 边界: 无(纯文件落盘/读取, 不碰 COS/LLM); 用 tmp_path 隔离, 不污染真实报告目录。
"""
import sys
import os
import json

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "rag"))
import run_eval


def _trace(i):
    return {
        "question": f"问题{i}", "question_type": "难点", "hit_score": 0.8,
        "hit": True, "score": 4, "judged": True, "rationale": "覆盖4/5",
        "answer": f"答案{i}",
        "recall": [{"key": f"ai-tutoring/04#{i}", "score": 0.8, "section": "04"}],
        "references": [{"file": "04-安全", "anchor": "a"}],
        "usage": {"cost_yuan": 0.01, "total_tokens": 100},
        "latency_ms": {"retrieve_ms": 100, "generate_ms": 200, "total_ms": 300},
        "version": "2026-08-24-test",
    }


def _agg():
    return {"count": 2, "hit_at_k_avg": 0.8, "quality_avg": 4.0, "judged_ratio": 1.0,
            "avg_latency_ms": 300, "total_cost_yuan": 0.02, "avg_cost_yuan": 0.01,
            "avg_tokens": 100, "hit_cases": 2, "unjudged": 0}


class TestTrace:
    """5.4 trace 落盘完整性"""

    def test_trace_saved_complete(self, tmp_path):
        results = [_trace(1), _trace(2)]
        path = run_eval._save_trace(results, eval_dir=str(tmp_path))
        assert os.path.exists(path)

        lines = [json.loads(l) for l in open(path, encoding="utf-8")]
        assert len(lines) == 2
        for t in lines:
            # 5.1 契约字段齐全
            for field in ("question", "question_type", "recall", "hit", "hit_score",
                          "answer", "references", "usage", "latency_ms", "score",
                          "rationale", "judged", "version"):
                assert field in t, f"trace 缺字段 {field}"
            assert "cost_yuan" in t["usage"]
            assert set(t["latency_ms"]) == {"retrieve_ms", "generate_ms", "total_ms"}

    def test_trace_single_backtrace(self, tmp_path):
        """单条回溯: 能按问题定位到一条 trace"""
        results = [_trace(1), _trace(2)]
        path = run_eval._save_trace(results, eval_dir=str(tmp_path))
        lines = [json.loads(l) for l in open(path, encoding="utf-8")]
        target = [t for t in lines if t["question"] == "问题2"][0]
        assert target["score"] == 4 and target["version"] == "2026-08-24-test"


class TestReport:
    """5.2 报告生成 + 5.3 版本对比"""

    def test_report_saved_with_version(self, tmp_path):
        report_dir = str(tmp_path / "reports")
        path = run_eval._save_report(_agg(), "2026-08-24-v2", "ai-tutoring", report_dir=report_dir)
        assert os.path.exists(path)
        assert "ai-tutoring-2026-08-24-v2.json" == os.path.basename(path)
        data = json.load(open(path, encoding="utf-8"))
        assert data["version"] == "2026-08-24-v2"
        assert data["module"] == "ai-tutoring"
        assert data["aggregate"]["hit_at_k_avg"] == 0.8

    def test_compare_selects_prev_report(self, tmp_path, capsys):
        """5.3 版本对比: 有历史报告时对比, 打印 delta"""
        report_dir = str(tmp_path / "reports")
        run_eval._save_report({"hit_at_k_avg": 0.7, "quality_avg": 3.0,
                               "total_cost_yuan": 0.05, "avg_latency_ms": 400},
                              "2026-08-24-v1", "ai-tutoring", report_dir=report_dir)
        new_agg = {"hit_at_k_avg": 0.8, "quality_avg": 4.0,
                   "total_cost_yuan": 0.06, "avg_latency_ms": 300}
        run_eval._compare(new_agg, "2026-08-24-v2", "ai-tutoring", report_dir=report_dir)
        out = capsys.readouterr().out
        assert "hit@k" in out and "0.8" in out
        assert "质量分" in out and "4.0" in out

    def test_compare_no_history_skips(self, tmp_path, capsys):
        report_dir = str(tmp_path / "empty")
        run_eval._compare(_agg(), "2026-08-24-v1", "ai-tutoring", report_dir=report_dir)
        out = capsys.readouterr().out
        assert "无历史报告" in out
