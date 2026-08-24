"""
3. 评测执行 - 跑评测集 → 出聚合报告(离线, 面试质量把关工具)

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 2A + 3 + 5
用法: cd ai-edu-ai-service && venv/bin/python scripts/rag/run_eval.py
输出: 逐条 trace + 聚合指标(hit@k / 质量分 / 耗时)

每条评测走真实检索原语(不降级, 暴露真实质量)。判分 LLM = doubao(复用现有链路)。
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.rag import eval_agent
import eval_dataset


def main():
    items = eval_dataset.load_dataset()
    print(f"评测集: {len(items)} 条, 开始评测(真实检索 + doubao 生成/判分)...\n")

    results = []
    for i, case in enumerate(items, 1):
        print(f"[{i}/{len(items)}] {case['question_type']}: {case['question']}")
        trace = eval_agent.run_eval_case(case)
        results.append(trace)
        print(f"    hit@3={trace['hit_score']:.2f} 质量分={trace['score']}/5"
              f" 判分={trace['judged']} 耗时={trace['latency_ms']['total_ms']}ms")
        if trace["rationale"]:
            print(f"    rationale: {trace['rationale'][:120]}")

    agg = eval_agent.aggregate(results)
    print("\n" + "=" * 50)
    print("聚合报告:")
    print(f"  条数: {agg['count']}")
    print(f"  hit@k 平均: {agg['hit_at_k_avg']:.3f} (命中 {agg['hit_cases']}/{agg['count']} 条)")
    print(f"  质量分平均: {agg['quality_avg']:.2f}/5 (判分 {agg['judged_ratio']:.0%})")
    print(f"  平均耗时: {agg['avg_latency_ms']}ms")

    # trace 落盘(5.1 简化: 本模块直接写 JSONL)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "eval", "trace_latest.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\ntrace 已落盘: {out}")


if __name__ == "__main__":
    main()
