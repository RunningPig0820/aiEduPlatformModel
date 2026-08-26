"""
任务 1.6⑥ 索引测试 - core/rag/query.py 编排核心 + 端点契约

覆盖(1.6 任务列表"索引测试"):
- 桶路由正确 / 幂等重建   → 已由 test_vector_store.py 覆盖(rag→RAG桶, --clear 幂等)
- 召回命中               → 向量路 key 进编排 / BM25 纯本地打分
- 锚定过滤               → classify 锁节 / 编排锚定加权(锁节块权重更高)
- 打分排序               → RRF × authority × 锚定; 完善文档(1.0)同分高于原始语料(0.7/0.8)
- text 反查              → 命中块 text 按 key 从 jsonl 反查
- API 契约返回结构       → api/rag.py 端点响应符合 1.6C(answer/references/intent/version)

Mock 边界 = query_vector(真实 COS 查询) + generate(doubao), 不碰真实 COS/LLM。
编排纯逻辑(BM25/classify/orchestrate)离线可测, 不 mock。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.rag import query as rag_core

# 测试语料: 两"块"分属完善文档(权威1.0)与语雀(0.7), 便于验证打分排序与锚定加权
BLOCKS = [
    {"text": "防套答案: 第1次要答案拦下给思路, count+1; 第2次才放行完整答案",
     "summary": "防作弊答案出口机制",
     "tags": {"module": "ai-tutoring", "section": "04", "source": "完善文档",
              "authority": 1.0, "file": "04-安全与防作弊", "file_path": "4.完善文档/04-安全与防作弊.md",
              "anchor": "04-安全与防作弊", "pool": "slice"}},
    {"text": "AI答疑面向小学到高中全学段, 启发式教学, 不直接给答案",
     "summary": "AI答疑定位与理念",
     "tags": {"module": "ai-tutoring", "section": "01", "source": "语雀",
              "authority": 0.7, "file": "语雀-答疑理念", "file_path": "1.语雀/答疑理念.md",
              "anchor": "答疑理念", "pool": "slice"}},
    {"text": "流式输出用 SSE, 前端逐字展示, 性能优化减少卡顿",
     "summary": "流式与性能",
     "tags": {"module": "ai-tutoring", "section": "07", "source": "代码",
              "authority": 0.8, "file": "分析-09-流式", "file_path": "3.代码/分析-09-流式.md",
              "anchor": "流式", "pool": "slice"}},
]


@pytest.fixture(autouse=True)
def stub_generate(monkeypatch):
    """默认 mock 掉 generate(不碰 doubao); 编排部分不受影响"""
    monkeypatch.setattr(rag_core, "generate", lambda hits, q: "mock 答案")


class TestClassify:
    """意图钩子: LLM 语义判断(闭集映射锁节) + 失败回退关键词"""

    def _fake_category(self, monkeypatch, cat):
        monkeypatch.setattr(rag_core, "_llm_category", lambda q: cat)

    def test_llm_category_maps_sections(self, monkeypatch):
        """LLM 返回闭集类别 → 映射锁节(项目介绍→01/03, 数据关联→05)"""
        self._fake_category(monkeypatch, "项目介绍")
        s = rag_core.classify("AI答疑是什么")
        assert s["locked_sections"] == ["01", "03"]
        assert s["strategy"] == "retrieve"

        self._fake_category(monkeypatch, "数据关联")
        assert rag_core.classify("掌握度怎么落库")["locked_sections"] == ["05"]

    def test_llm_category_other_empty(self, monkeypatch):
        """LLM 判'其他' → 不锁任何节(不锚定, 全量加权)"""
        self._fake_category(monkeypatch, "其他")
        assert rag_core.classify("讲讲天气")["locked_sections"] == []

    def test_llm_fail_fallback_anchor(self, monkeypatch):
        """LLM 失败/非闭集 → 回退关键词锚定(不空锁, 保底)"""
        monkeypatch.setattr(rag_core, "_llm_category", lambda q: "非闭集垃圾")
        s = rag_core.classify("怎么防学生套答案？")
        assert "04" in s["locked_sections"]  # 关键词命中 04/07

    def test_fallback_anchor_locks_04_07(self):
        """关键词锚定直接验证: 防套答案 → 04/07"""
        locked = rag_core._fallback_anchor("怎么防学生套答案？")
        assert "04" in locked and "07" in locked

    def test_fallback_anchor_no_anchor_empty(self):
        assert rag_core._fallback_anchor("讲讲天气") == set()


class TestBM25:
    """BM25 召回单元: 纯本地打分"""

    def test_bm25_hits_relevant(self):
        r = rag_core.retrieve_bm25("怎么防学生套答案", BLOCKS)
        keys = [h["key"] for h in r["hits"]]
        assert keys and "04-安全与防作弊" in keys[0]  # 防套答案相关块排前
        assert all(h["bm25_score"] > 0 for h in r["hits"])


class TestOrchestrate:
    """编排器: RRF × authority × 锚定加权"""

    def test_fusion_rank_authority_boost(self, monkeypatch):
        # mock LLM 意图分类(避免真实 doubao 调用), 直接锁 04/07(难点)
        monkeypatch.setattr(rag_core, "_llm_category", lambda q: "难点")
        strategy = rag_core.classify("怎么防学生套答案")
        # 向量路: 返回与 BM25 相同的 04 块(模拟两路都命中)
        vec = {"hits": [{"key": "rag-slice/04-安全与防作弊/04-安全与防作弊#0", "distance": 0.1}],
               "confidence": 0.9}
        bm = rag_core.retrieve_bm25("怎么防学生套答案", BLOCKS)
        hits = rag_core.orchestrate("怎么防学生套答案", BLOCKS, vec, bm, strategy, top_k=5)
        assert hits
        # 锚定锁 04 → 完善文档 04 块加权 1.5 → 排第一
        assert hits[0]["file"] == "04-安全与防作弊"
        assert hits[0]["authority"] == 1.0
        assert hits[0]["section"] == "04"

    def test_text_backref_by_key(self):
        """text 反查: 命中块 text 从 jsonl 反查(不依赖向量路 metadata)"""
        strategy = {"locked_sections": [], "strategy": "retrieve"}
        vec = {"hits": [], "confidence": 0.0}
        bm = {"hits": [{"key": "rag-slice/04-安全与防作弊/04-安全与防作弊#0", "bm25_score": 8.0}],
              "confidence": 0.8}
        hits = rag_core.orchestrate("防套答案", BLOCKS, vec, bm, strategy, top_k=1)
        assert hits[0]["text"].startswith("防套答案")  # text 按 key 从语料反查到
        assert hits[0]["file_path"] == "4.完善文档/04-安全与防作弊.md"

    def test_score_authority_sorted(self):
        """打分排序: 两路同命中时 authority 高者在前(完善1.0 > 语雀0.7)"""
        strategy = {"locked_sections": [], "strategy": "retrieve"}
        both = [
            {"key": "rag-slice/04-安全与防作弊/04-安全与防作弊#0", "distance": 0.05},
            {"key": "rag-slice/语雀-答疑理念/答疑理念#0", "distance": 0.06},
        ]
        vec = {"hits": both, "confidence": 0.9}
        bm = {"hits": [{"key": h["key"], "bm25_score": 8.0} for h in both], "confidence": 0.8}
        hits = rag_core.orchestrate("测试", BLOCKS, vec, bm, strategy, top_k=5)
        assert hits[0]["authority"] >= hits[1]["authority"]  # 权威度加权后降序


class TestRagAPI:
    """API 契约(1.6C): POST /api/tutoring/rag/query 返回结构"""

    @pytest.fixture(autouse=True)
    def mock_intent_llm(self, monkeypatch):
        """API 全链路 mock 掉 LLM 意图(避免真实 doubao), 统一判 ai-tutoring + 难点/开发难点"""
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": {
            "anchor": "ai-tutoring", "category": "难点", "categories": ["开发难点"],
            "switch_detected": False, "ambiguous": False, "candidates": []})

    def setup_method(self):
        from api.rag import router as rag_router
        app = FastAPI()
        app.include_router(rag_router)
        self.client = TestClient(app)
        from config.settings import settings
        self.auth = {"x-internal-token": settings.INTERNAL_TOKEN}

    def _dual_hit(self, q):
        """双池召回 mock: 全量池命中 04 块, 切片/BM25 空"""
        return {"full": {"hits": [{"key": "rag-slice/04-安全与防作弊/04-安全与防作弊#0",
                                   "distance": 0.1}], "confidence": 0.9},
                "slice": {"hits": [], "confidence": 0.0},
                "bm25": {"hits": [], "confidence": 0.0}}

    def test_query_contract_shape(self, monkeypatch):
        """返回结构: answer/references/intent/version(契约字段齐全)"""
        # 用测试语料替换双池加载 + mock 双池召回
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_dual", self._dual_hit)
        monkeypatch.setattr(rag_core, "generate", lambda hits, q: "面试口述答案")

        r = self.client.post("/api/tutoring/rag/query",
                             json={"question": "怎么防学生套答案？"}, headers=self.auth)
        assert r.status_code == 200
        body = r.json()
        assert set(("answer", "references", "intent", "version")) <= set(body)
        ref = body["references"][0]
        assert set(("file", "file_path", "anchor", "authority", "summary")) <= set(ref)
        assert ref["file_path"] == "4.完善文档/04-安全与防作弊.md"
        assert body["intent"]["strategy"] == "retrieve"

    def test_query_no_hit_refuses(self, monkeypatch):
        """降级语义3: 无命中 → 拒答不编造"""
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_dual",
                            lambda q: {"full": {"hits": [], "confidence": 0.0},
                                       "slice": {"hits": [], "confidence": 0.0},
                                       "bm25": {"hits": [], "confidence": 0.0}})

        r = self.client.post("/api/tutoring/rag/query",
                             json={"question": "今天天气如何"}, headers=self.auth)
        assert r.status_code == 200
        assert "未覆盖" in r.json()["answer"]

    def test_query_vector_fail_degrade_bm25(self, monkeypatch):
        """降级语义1: COS 向量挂了 → 降级纯 BM25, references 仍返回"""
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_dual",
                            lambda q: (_ for _ in ()).throw(RuntimeError("cos down")))

        r = self.client.post("/api/tutoring/rag/query",
                             json={"question": "怎么防套答案"}, headers=self.auth)
        assert r.status_code == 200
        assert r.json()["references"]  # BM25 路兜底, 仍有命中
        assert "04" in r.json()["references"][0]["file"]

    def test_query_generate_fail_degrade_references(self, monkeypatch):
        """降级语义2: doubao 挂了 → references 当答案, 不空答"""
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_dual", self._dual_hit)
        monkeypatch.setattr(rag_core, "generate",
                            lambda hits, q: (_ for _ in ()).throw(RuntimeError("doubao down")))

        r = self.client.post("/api/tutoring/rag/query",
                             json={"question": "怎么防套答案"}, headers=self.auth)
        assert r.status_code == 200
        assert "生成服务不可用" in r.json()["answer"]  # 降级为召回清单
        assert r.json()["references"]

    def test_query_missing_token_403(self):
        r = self.client.post("/api/tutoring/rag/query", json={"question": "问"})
        assert r.status_code == 403

    def test_query_wrong_token_403(self):
        r = self.client.post("/api/tutoring/rag/query",
                             json={"question": "问"}, headers={"x-internal-token": "wrong"})
        assert r.status_code == 403


class TestMultiModule:
    """1.13 多模块: intent 9类 categories + retrieve_dual 模块/类别本地过滤"""

    def _fake_intent(self, monkeypatch, **over):
        base = {"anchor": "ai-tutoring", "category": "难点", "categories": ["开发难点"],
                "switch_detected": False, "ambiguous": False, "candidates": []}
        base.update(over)
        monkeypatch.setattr(rag_core, "_llm_intent", lambda q, h, current_project="ai-tutoring": base)

    def test_intent_uses_llm_categories(self, monkeypatch):
        """LLM 输出 categories(9类) → locked_categories 直接用, 不走 6→9 映射"""
        self._fake_intent(monkeypatch, anchor="rag-system", category="架构", categories=["架构设计"])
        it = rag_core.intent("RAG 怎么多路召回")
        assert it["anchor"] == "rag-system"
        assert it["locked_categories"] == ["架构设计"]

    def test_intent_empty_categories_no_filter(self, monkeypatch):
        """LLM categories 空 → 全局查询不筛(去掉 6→9 映射兜底)"""
        self._fake_intent(monkeypatch, categories=[])
        assert rag_core.intent("怎么防学生套答案")["locked_categories"] == []

    def test_intent_missing_categories_field_no_filter(self, monkeypatch):
        """LLM 未给 categories 字段 → 同样全局查询不筛"""
        self._fake_intent(monkeypatch, categories=None)
        it = rag_core.intent("怎么防学生套答案")
        assert it["locked_categories"] == []

    def test_intent_sanitize_non_closed_categories(self):
        """_sanitize_intent: LLM categories 含非 9 类闭集值 → 过滤只留闭集"""
        raw = {"anchor": "ai-tutoring", "category": "难点",
               "categories": ["开发难点", "瞎写类别"],
               "switch_detected": False, "ambiguous": False, "candidates": []}
        out = rag_core._sanitize_intent(raw, "防套答案")
        assert out["categories"] == ["开发难点"]

    def test_retrieve_dual_bm25_filters_module_and_category(self, monkeypatch):
        """retrieve_dual 本地 BM25: 按 module 筛(全量池) + 切片池按 category 筛后再打分"""
        multi = [
            {"text": "AI答疑防套答案机制", "summary": "s",
             "tags": {"module": "ai-tutoring", "section": "04", "source": "完善文档",
                      "authority": 1.0, "file": "f1", "file_path": "p1", "anchor": "a1",
                      "category": "开发难点", "pool": "slice"}},
            {"text": "RAG 多路召回 RRF 融合", "summary": "s",
             "tags": {"module": "rag-system", "section": "", "source": "代码",
                      "authority": 0.8, "file": "f2", "file_path": "p2", "anchor": "a2",
                      "category": "架构设计", "pool": "slice"}},
            {"text": "RAG 全量池整篇文档", "summary": "s",
             "tags": {"module": "rag-system", "section": "", "source": "完善文档",
                      "authority": 1.0, "file": "f3", "file_path": "p3", "anchor": "a3",
                      "category": "架构设计", "pool": "full"}},
        ]
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: multi)
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q, vector_type="rag", module=None, categories=None: {"hits": [], "confidence": 0.0})
        dual = rag_core.retrieve_dual("RAG 召回", corpus="rag-system", locked_categories=["架构设计"])
        bm_keys = [h["key"] for h in dual["bm25"]["hits"]]
        assert bm_keys, "BM25 应有命中"
        assert all("f1" not in k for k in bm_keys)  # ai-tutoring 块被模块筛掉
        assert any("rag-slice/f2" in k for k in bm_keys) or any("rag-full/f3" in k for k in bm_keys)


class TestRagSource:
    """U4: /api/rag/source 读 COS 普通桶("查看原文")"""

    def setup_method(self):
        from api.rag import SOURCE_ROUTER
        app = FastAPI()
        app.include_router(SOURCE_ROUTER)
        self.client = TestClient(app)
        from config.settings import settings
        self.auth = {"x-internal-token": settings.INTERNAL_TOKEN}

    def _fake_client(self, monkeypatch, body=b"# md"):
        """mock get_normal_cos_client → 返回记录调用 key 的假 client"""
        class _Stream:
            def __init__(self, b):
                self._b = b
            def get_raw_stream(self):
                return self
            def read(self):
                return self._b
        class FakeClient:
            def __init__(self, b):
                self.calls = []
                self._b = b
            def get_object(self, Bucket, Key):
                self.calls.append(Key)
                return {"Body": _Stream(self._b)}
        fc = FakeClient(body)
        monkeypatch.setattr("api.rag.get_normal_cos_client", lambda: fc)
        return fc

    def test_source_returns_md(self, monkeypatch):
        """按 COS key 取回 md 内容(路径中文需 URL 编码, 与前端一致)"""
        from urllib.parse import quote
        body = "# 坑档案".encode("utf-8")
        fc = self._fake_client(monkeypatch, body=body)
        key = "rag-slices/ai-tutoring/坑档案/坑档案-J1.md"
        url = "/api/rag/source/" + "/".join(quote(seg) for seg in key.split("/"))
        r = self.client.get(url, headers=self.auth)
        assert r.status_code == 200
        assert r.text == "# 坑档案"
        assert fc.calls == [key]

    def test_source_403_no_token(self):
        r = self.client.get("/api/rag/source/rag-slices/x.md")
        assert r.status_code == 403

    def test_source_404_invalid_prefix(self, monkeypatch):
        """非 rag-source/rag-slices 前缀 → 404(防任意 COS key)"""
        self._fake_client(monkeypatch)
        r = self.client.get("/api/rag/source/foo/bar.md", headers=self.auth)
        assert r.status_code == 404

    def test_source_404_cos_missing(self, monkeypatch):
        """COS 读不到 → 404"""
        class Failing:
            def get_object(self, **kw):
                raise Exception("no such key")
        monkeypatch.setattr("api.rag.get_normal_cos_client", lambda: Failing())
        r = self.client.get("/api/rag/source/rag-slices/x.md", headers=self.auth)
        assert r.status_code == 404
