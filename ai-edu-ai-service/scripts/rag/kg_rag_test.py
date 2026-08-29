"""knowledge-graph RAG 单模块 + 多模块隔离测试(2026-08-29)。

1. 向量路可用性检查(embed 一次)
2. 单模块: corpus=knowledge-graph 查 kg 代表性问题 → 验证命中全来自 kg
3. 多模块隔离: 同一问题分别指定 ai-tutoring / knowledge-graph corpus → 验证 module 过滤(不混入他模块)
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.rag import query as rag_core


def mod_of(h):
    """orchestrate hit 无 module 顶层字段, 用 file_path 判断模块。"""
    fp = h.get("file_path", "")
    if "knowledge-graph" in fp:
        return "knowledge-graph"
    if "ai-tutoring" in fp:
        return "ai-tutoring"
    if "question-analysis" in fp:
        return "question-analysis"
    return "?"


KG_QS = [
    "知识点匹配率怎么从17%提高到97.1%",
    "为什么用 Neo4j 不用 MySQL 或 ES",
    "前置依赖和教学顺序有什么区别",
    "llmTaskLock 断点续传是怎么实现的",
    "知识图谱的节点和关系类型有哪些",
    "课标知识点怎么加工进图谱的",
]

def check_vector():
    """向量路可用性(embed 一次)。"""
    try:
        from core.tutoring.vector_store import embed
        v = embed("测试向量路")
        return True, f"向量路可用(dim={len(v)})"
    except Exception as e:
        return False, f"向量路不可用: {str(e)[:120]}"


def single_module_test():
    print("=" * 60)
    print("【单模块测试】corpus=knowledge-graph, 6 问")
    print("=" * 60)
    blocks = rag_core._load_all_blocks()
    for q in KG_QS:
        try:
            dual = rag_core.retrieve_dual(q, corpus="knowledge-graph")
            note = "向量路"
        except Exception as e:
            bm_pool = rag_core.select_corpus(blocks, "knowledge-graph")
            dual = {"full": {"hits": [], "confidence": 0.0},
                    "slice": {"hits": [], "confidence": 0.0},
                    "slice_q": {"hits": [], "confidence": 0.0},
                    "bm25": rag_core.retrieve_bm25(q, bm_pool)}
            note = "BM25"
        it = {"anchor": "knowledge-graph", "locked_sections": (), "locked_categories": None}
        hits = rag_core.orchestrate(q, blocks, dual["full"], dual["bm25"], it,
                                    top_k=5, vec2_result=dual["slice"],
                                    vec3_result=dual["slice_q"], corpus="knowledge-graph")
        if not hits:
            print(f"  [无命中] {q}")
            continue
        mods = {mod_of(h) for h in hits}
        srcs = {h.get("source") for h in hits}
        cross = mods - {"knowledge-graph"}
        flag = "✓" if not cross else "✗ 混入他模块!"
        print(f"  {flag} {q[:26]:<28} → {len(hits)} hits | 模块 {mods} | 来源 {srcs}")
        for h in hits[:3]:
            print(f"      [{h.get('source')}] {h['file'][:36]} 权威{h.get('authority')} 分{h.get('score',0):.3f}")


def multi_module_isolation():
    print()
    print("=" * 60)
    print("【多模块隔离】同问题在不同 corpus 下召回应互不混入")
    print("=" * 60)
    blocks = rag_core._load_all_blocks()
    q = "知识点匹配率怎么从17%提高到97.1%"
    for corpus in ("knowledge-graph", "ai-tutoring", "question-analysis"):
        try:
            dual = rag_core.retrieve_dual(q, corpus=corpus)
            note = "向量路"
        except Exception as e:
            bm_pool = rag_core.select_corpus(blocks, corpus)
            dual = {"full": {"hits": [], "confidence": 0.0},
                    "slice": {"hits": [], "confidence": 0.0},
                    "slice_q": {"hits": [], "confidence": 0.0},
                    "bm25": rag_core.retrieve_bm25(q, bm_pool)}
            note = "BM25"
        it = {"anchor": corpus, "locked_sections": (), "locked_categories": None}
        hits = rag_core.orchestrate(q, blocks, dual["full"], dual["bm25"], it,
                                    top_k=3, vec2_result=dual["slice"],
                                    vec3_result=dual["slice_q"], corpus=corpus)
        mods = {mod_of(h) for h in hits} if hits else set()
        ok = mods <= {corpus}
        print(f"  corpus={corpus:<20} → {len(hits)} hits | 命中模块 {mods or '∅'} | {'✓隔离' if ok else '✗ 泄漏'}")
        for h in hits[:2]:
            print(f"      [{h.get('source')}] {h['file'][:40]}")


if __name__ == "__main__":
    ok, note = check_vector()
    print(f"[向量路] {note}")
    print()
    single_module_test()
    multi_module_isolation()
