"""
M6 ① 引导底座池测试 - core/rag/guide_pool.py（2026-08-26）

覆盖(后端 M6 方案 ①):
- GUIDE_POOL 结构: ai-tutoring 池含 5 方向, 主方向非空, rag 组是子集
- scope_questions: 全部去重保序; directions 限定; 未知模块 → FALLBACK
- pool_for: 未知/缺省 → FALLBACK_MODULE
- 数据源对齐: 去重后数量 = 引导问题.md 编号题数(75)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

from core.rag import guide_pool


class TestGuidePool:
    def test_ai_tutoring_pool_directions(self):
        """ai-tutoring 池含 5 方向且主方向非空"""
        pool = guide_pool.GUIDE_POOL["ai-tutoring"]
        assert set(pool) >= {"intro", "operation", "data_relation", "difficulty", "rag"}
        for d in ("intro", "operation", "data_relation", "difficulty"):
            assert pool[d], f"{d} 非空"
        assert pool["rag"], "rag 桥接子集非空"

    def test_rag_is_subset(self):
        """rag 组 ⊆ 主方向池(桥接子集, scope 去重后不新增)"""
        scope = set(guide_pool.scope_questions("ai-tutoring"))
        assert set(guide_pool.GUIDE_POOL["ai-tutoring"]["rag"]) <= scope

    def test_scope_dedup_preserve_order(self):
        """scope_questions 全部去重保序"""
        qs = guide_pool.scope_questions("ai-tutoring")
        assert len(qs) == len(set(qs))
        assert qs == list(dict.fromkeys(qs))

    def test_scope_directions_filter(self):
        """directions 限定 → 只出该方向(rag 组去重)"""
        rag = guide_pool.scope_questions("ai-tutoring", ("rag",))
        assert rag == list(dict.fromkeys(guide_pool.GUIDE_POOL["ai-tutoring"]["rag"]))

    def test_pool_for_fallback(self):
        """未知/缺省模块 → FALLBACK_MODULE 池"""
        assert guide_pool.pool_for(None) is guide_pool.GUIDE_POOL[guide_pool.FALLBACK_MODULE]
        assert guide_pool.pool_for("unknown-module") is guide_pool.GUIDE_POOL["ai-tutoring"]
        assert guide_pool.pool_for("ai-tutoring") is guide_pool.GUIDE_POOL["ai-tutoring"]

    def test_scope_unknown_module(self):
        """未知模块 scope → FALLBACK 池(不崩)"""
        assert guide_pool.scope_questions("rag-system") == \
            guide_pool.scope_questions(guide_pool.FALLBACK_MODULE)

    def test_count_matches_source(self):
        """数据源对齐: 75 题全部入库(引导问题.md 编号 1~75)"""
        assert len(guide_pool.scope_questions("ai-tutoring")) == 75

    def test_questions_sane(self):
        """池内问题非空且为具体问句(防空项/占位; 可答性本身由评测验证)"""
        for q in guide_pool.scope_questions("ai-tutoring"):
            assert isinstance(q, str) and len(q.strip()) >= 4, f"空泛/占位: {q!r}"


class TestEntryPool:
    def test_entry_nonempty_with_rag(self):
        """入口池非空且含 ≥1 条 rag 方向入口题(guide 必含 rag 方向的来源)"""
        entry = guide_pool.entry_for("ai-tutoring")
        assert len(entry) >= 3
        assert any(d == "rag" for d, _ in entry)

    def test_entry_questions_simple(self):
        """入口问题是入门级(一看就懂能直接点): 短句式 + 无技术难点特征词"""
        hard_kws = ("50~145", "LangGraph", "ActionMeta", "SSE", "Neo4j", "护栏",
                    "P0", "JSON", "并发", "熔断", "提示词注入", "掌握度", "题型")
        for d, q in guide_pool.entry_for("ai-tutoring"):
            assert len(q) <= 20, f"入口题过长, 用户看不懂: {q}"
            assert not any(k in q for k in hard_kws), f"入口题偏难, 割裂距离: {q}"

    def test_entry_scope_disjoint_from_scope(self):
        """entry 不进 scope_questions(主池 75 题不受影响; 入口是引导专用)"""
        assert len(guide_pool.scope_questions("ai-tutoring")) == 75

    def test_entry_templated_per_module(self):
        """入口引导用模块中文名动态生成, 不写死"AI答疑"(多模块通用)"""
        for mod, zh in (("ai-tutoring", "AI答疑"), ("rag-system", "RAG项目"),
                        ("knowledge-graph", "知识图谱"), ("question-analysis", "题型分析")):
            entry = guide_pool.entry_for(mod)
            questions = [q for _, q in entry]
            assert any(zh in q for q in questions), f"{mod} 入口题应含模块名 {zh}: {questions}"
            assert not any("AI答疑" in q and zh != "AI答疑" for q in questions), \
                f"{mod} 入口题误带他模块名 AI答疑: {questions}"

    def test_entry_unknown_module_fallback(self):
        """未知/缺省模块 → 模板 + FALLBACK_MODULE 中文名(AI答疑), 不崩"""
        for mod in ("unknown-module", None):
            entry = guide_pool.entry_for(mod)
            assert entry
            assert any("AI答疑" in q for _, q in entry)
            assert all(isinstance(d, str) for d, _ in entry)

    def test_entry_override_honored(self):
        """每模块可覆盖: entry 组存在则优先(用于定制入口重点)"""
        from core.rag import guide_pool as gp
        saved = gp.GUIDE_POOL.get("ai-tutoring", {}).get("entry")
        try:
            gp.GUIDE_POOL["ai-tutoring"]["entry"] = [("intro", "定制入口题")]
            assert [q for _, q in gp.entry_for("ai-tutoring")] == ["定制入口题"]
        finally:
            if saved is not None:
                gp.GUIDE_POOL["ai-tutoring"]["entry"] = saved
            else:
                gp.GUIDE_POOL["ai-tutoring"].pop("entry", None)
