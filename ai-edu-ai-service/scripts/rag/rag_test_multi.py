"""全量多模块轮询测试(2026-08-29)。

4 个模块(ai-tutoring/question-analysis/knowledge-graph/rag-system)轮着提问,
验证: ① 模块隔离(corpus 过滤, 命中全来自指定模块) ② 召回非空且相关 ③ 展示 top 命中。
向量路可用时走向量, 否则降级 BM25。
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.rag import query as rag_core

def mod_of(h):
    fp = h.get("file_path", "")
    for m in ("knowledge-graph", "ai-tutoring", "question-analysis", "rag-system"):
        if m in fp:
            return m
    return "?"

MODULE_QS = {
    "ai-tutoring": [
        "怎么防止学生套答案",
        "掌握度是怎么计算的",
        "图片题是怎么处理的",
    ],
    "question-analysis": [
        "题型怎么动态聚类的",
        "题型分析和知识图谱怎么联动",
    ],
    "knowledge-graph": [
        "知识点匹配率怎么从17%提高到97.1%",
        "为什么用 Neo4j 不用 MySQL 或 ES",
        "前置依赖和教学顺序有什么区别",
    ],
    "rag-system": [
        "RAG问答系统是干什么的",
        "双池检索设计是什么样的",
        "两道门怎么协同工作的",
    ],
}

def run():
    blocks = rag_core._load_all_blocks()
    print("=" * 64)
    print("全量多模块轮询测试: 4 模块 × 代表性问题")
    print("=" * 64)
    total, ok_mod, empty = 0, 0, 0
    for module, qs in MODULE_QS.items():
        print(f"\n── {module} ──")
        for q in qs:
            try:
                dual = rag_core.retrieve_dual(q, corpus=module)
                note = "向量"
            except Exception:
                pool = rag_core.select_corpus(blocks, module)
                dual = {"full": {"hits": [], "confidence": 0}, "slice": {"hits": [], "confidence": 0},
                        "slice_q": {"hits": [], "confidence": 0}, "bm25": rag_core.retrieve_bm25(q, pool)}
                note = "BM25"
            it = {"anchor": module, "locked_sections": (), "locked_categories": None}
            hits = rag_core.orchestrate(q, blocks, dual["full"], dual["bm25"], it,
                                        top_k=3, vec2_result=dual["slice"],
                                        vec3_result=dual["slice_q"], corpus=module)
            total += 1
            if not hits:
                print(f"  [空] [{note}] {q[:24]}")
                empty += 1
                continue
            mods = {mod_of(h) for h in hits}
            leak = mods - {module}
            if not leak:
                ok_mod += 1
                flag = "✓"
            else:
                flag = "✗ 泄漏→" + str(leak)
            print(f"  {flag} [{note}] {q[:24]:<26} → {len(hits)}hits 模块{mods}")
            for h in hits[:2]:
                print(f"      [{h.get('source')}] {h['file'][:38]:<40} a{h.get('authority')} s{h.get('score',0):.3f}")
    print("\n" + "=" * 64)
    print(f"结果: {total} 问 | 隔离正确 {ok_mod} | 空召回 {empty} | 泄漏 {total - ok_mod - empty}")
    print("=" * 64)

if __name__ == "__main__":
    run()
