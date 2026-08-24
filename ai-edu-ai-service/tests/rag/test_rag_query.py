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
              "anchor": "04-安全与防作弊"}},
    {"text": "AI答疑面向小学到高中全学段, 启发式教学, 不直接给答案",
     "summary": "AI答疑定位与理念",
     "tags": {"module": "ai-tutoring", "section": "01", "source": "语雀",
              "authority": 0.7, "file": "语雀-答疑理念", "file_path": "1.语雀/答疑理念.md",
              "anchor": "答疑理念"}},
    {"text": "流式输出用 SSE, 前端逐字展示, 性能优化减少卡顿",
     "summary": "流式与性能",
     "tags": {"module": "ai-tutoring", "section": "07", "source": "代码",
              "authority": 0.8, "file": "分析-09-流式", "file_path": "3.代码/分析-09-流式.md",
              "anchor": "流式"}},
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
        vec = {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "distance": 0.1}],
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
        bm = {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "bm25_score": 8.0}],
              "confidence": 0.8}
        hits = rag_core.orchestrate("防套答案", BLOCKS, vec, bm, strategy, top_k=1)
        assert hits[0]["text"].startswith("防套答案")  # text 按 key 从语料反查到
        assert hits[0]["file_path"] == "4.完善文档/04-安全与防作弊.md"

    def test_score_authority_sorted(self):
        """打分排序: 两路同命中时 authority 高者在前(完善1.0 > 语雀0.7)"""
        strategy = {"locked_sections": [], "strategy": "retrieve"}
        both = [
            {"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "distance": 0.05},
            {"key": "ai-tutoring/语雀-答疑理念/答疑理念#0", "distance": 0.06},
        ]
        vec = {"hits": both, "confidence": 0.9}
        bm = {"hits": [{"key": h["key"], "bm25_score": 8.0} for h in both], "confidence": 0.8}
        hits = rag_core.orchestrate("测试", BLOCKS, vec, bm, strategy, top_k=5)
        assert hits[0]["authority"] >= hits[1]["authority"]  # 权威度加权后降序


class TestRagAPI:
    """API 契约(1.6C): POST /api/tutoring/rag/query 返回结构"""

    @pytest.fixture(autouse=True)
    def mock_intent_llm(self, monkeypatch):
        """API 全链路 mock 掉 LLM 意图分类(避免真实 doubao), 统一按'难点'锁 04/07"""
        monkeypatch.setattr(rag_core, "_llm_category", lambda q: "难点")

    def setup_method(self):
        from api.rag import router as rag_router
        app = FastAPI()
        app.include_router(rag_router)
        self.client = TestClient(app)
        from config.settings import settings
        self.auth = {"x-internal-token": settings.INTERNAL_TOKEN}

    def test_query_contract_shape(self, monkeypatch):
        """返回结构: answer/references/intent/version(契约字段齐全)"""
        # 用测试语料替换 DATA 加载 + mock 向量路
        monkeypatch.setattr(rag_core, "_load_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0",
                                                  "distance": 0.1}], "confidence": 0.9})
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
        monkeypatch.setattr(rag_core, "_load_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_vector", lambda q: {"hits": [], "confidence": 0.0})
        monkeypatch.setattr(rag_core, "retrieve_bm25",
                            lambda q, b: {"hits": [], "confidence": 0.0})

        r = self.client.post("/api/tutoring/rag/query",
                             json={"question": "今天天气如何"}, headers=self.auth)
        assert r.status_code == 200
        assert "未覆盖" in r.json()["answer"]

    def test_query_vector_fail_degrade_bm25(self, monkeypatch):
        """降级语义1: COS 向量挂了 → 降级纯 BM25, references 仍返回"""
        monkeypatch.setattr(rag_core, "_load_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: (_ for _ in ()).throw(RuntimeError("cos down")))

        r = self.client.post("/api/tutoring/rag/query",
                             json={"question": "怎么防套答案"}, headers=self.auth)
        assert r.status_code == 200
        assert r.json()["references"]  # BM25 路兜底, 仍有命中
        assert "04" in r.json()["references"][0]["file"]

    def test_query_generate_fail_degrade_references(self, monkeypatch):
        """降级语义2: doubao 挂了 → references 当答案, 不空答"""
        monkeypatch.setattr(rag_core, "_load_blocks", lambda: BLOCKS)
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0",
                                                  "distance": 0.1}], "confidence": 0.9})
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
