"""
4+5. 评测执行 + 报告生成 - 跑评测集 → 聚合报告(含 cost/latency) → trace 落盘 → 版本对比

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 2A + 3 + 4 + 5
用法: cd ai-edu-ai-service && venv/bin/python scripts/rag/run_eval.py [--compare]
输出:
  - 逐条 trace(cost/latency/usage) → data/eval/trace_latest.jsonl
  - 聚合报告(hit@k/质量分/cost/latency) → data/eval/reports/<version>.json
  - --compare: 与上一份报告对比 hit@k/质量分变化(5.3)

每条评测走真实检索原语(不降级, 暴露真实质量)。判分 LLM = doubao(复用现有链路)。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.rag import eval_agent
import eval_dataset

EVAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "eval")
TRACE_PATH = os.path.join(EVAL_DIR, "trace_latest.jsonl")
REPORT_DIR = os.path.join(EVAL_DIR, "reports")


def _save_trace(results, eval_dir: str = EVAL_DIR) -> str:
    os.makedirs(eval_dir, exist_ok=True)
    path = os.path.join(eval_dir, "trace_latest.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def _save_report(agg: dict, version: str, report_dir: str = REPORT_DIR) -> str:
    os.makedirs(report_dir, exist_ok=True)
    path = os.path.join(report_dir, f"{version}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": version, "aggregate": agg}, f, ensure_ascii=False, indent=2)
    return path


def _list_reports(report_dir: str = REPORT_DIR) -> list:
    if not os.path.isdir(report_dir):
        return []
    return sorted(os.listdir(report_dir))


def _compare(agg: dict, version: str, report_dir: str = REPORT_DIR):
    """5.3 报告版本对比: 与上一份报告对比 hit@k/质量分变化"""
    reports = [f for f in _list_reports(report_dir) if f.endswith(".json") and f != f"{version}.json"]
    if not reports:
        print("\n[版本对比] 无历史报告, 跳过(下次运行可对比)")
        return
    prev_path = os.path.join(report_dir, reports[-1])
    with open(prev_path, encoding="utf-8") as f:
        prev = json.load(f)["aggregate"]
    print("\n" + "=" * 50)
    print("版本对比(与上一份):")
    for key, label in [("hit_at_k_avg", "hit@k"), ("quality_avg", "质量分"),
                       ("total_cost_yuan", "总成本"), ("avg_latency_ms", "平均耗时")]:
        delta = agg[key] - prev.get(key, 0)
        arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "=")
        print(f"  {label:8s} {prev.get(key, 0):>8} → {agg[key]:>8}  {arrow} {delta:+.3f}")


def run_evaluation() -> dict:
    """执行评测(可复用: CLI/API 共用)。

    返回 {results, aggregate, version, trace_path, report_path}。
    """
    items = eval_dataset.load_dataset()
    print(f"评测集: {len(items)} 条, 开始评测(真实检索 + doubao 生成/判分)...\n")

    results = []
    for i, case in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {case['question_type']}: {case['question']}")
        trace = eval_agent.run_eval_case(case)
        results.append(trace)
        u = trace["usage"]
        print(f"    hit@{eval_agent.HIT_K}={trace['hit_score']:.2f} 质量分={trace['score']}/5"
              f" 耗时={trace['latency_ms']['total_ms']}ms"
              f" tokens={u['total_tokens']} cost=¥{u['cost_yuan']:.4f}")
        if trace["rationale"]:
            print(f"    rationale: {trace['rationale'][:110]}")

    version = results[0]["version"] if results else ""
    agg = eval_agent.aggregate(results)
    trace_path = _save_trace(results)
    report_path = _save_report(agg, version)
    return {"results": results, "aggregate": agg, "version": version,
            "trace_path": trace_path, "report_path": report_path}


def _print_report(out: dict, compare: bool = False):
    agg = out["aggregate"]
    print("\n" + "=" * 50)
    print(f"聚合报告(语料版本 {out['version']}):")
    print(f"  条数: {agg['count']}")
    print(f"  hit@k 平均: {agg['hit_at_k_avg']:.3f} (命中 {agg['hit_cases']}/{agg['count']} 条)")
    print(f"  precision@{eval_agent.HIT_K} 平均: {agg.get('precision_at_k_avg', 0):.3f} (top-{eval_agent.HIT_K} 相关块占比)")
    print(f"  quoted 合法率: {agg.get('quoted_valid_ratio', 0):.0%} (quotedKeys ⊆ 召回块)")
    print(f"  质量分平均: {agg['quality_avg']:.2f}/5 (判分 {agg['judged_ratio']:.0%})")
    print(f"  平均耗时: {agg['avg_latency_ms']}ms")
    print(f"  总成本: ¥{agg['total_cost_yuan']:.4f} (均 ¥{agg['avg_cost_yuan']:.4f}, 均 {agg['avg_tokens']} tokens)")
    print(f"\ntrace 已落盘: {out['trace_path']}")
    print(f"报告已落盘: {out['report_path']}")
    if compare:
        _compare(agg, out["version"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--compare", action="store_true", help="与上一份报告对比(5.3)")
    args = ap.parse_args()

    out = run_evaluation()
    _print_report(out, compare=args.compare)


if __name__ == "__main__":
    main()
