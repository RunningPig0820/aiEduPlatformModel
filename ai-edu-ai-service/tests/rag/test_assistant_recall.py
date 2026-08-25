"""
A3 recall 双路 + anchor 选池测试 - assistant.recall + query.select_corpus/orchestrate corpus

覆盖(tasks E 组"anchor 选池测试: orchestrate corpus 参数、锚定公式不变" + "双路超时降级测试"):
- select_corpus: anchor 闭集内过滤模块池; 空/非闭集 → 全池; 无语料模块 → 空池
- orchestrate corpus: 传 corpus 先按模块过滤再融合; 锚定公式原样(节级加权不变)
- recall 双路: 向量 + BM25 都命中 → 无 degraded
- recall 超时降级: 向量路超时/异常 → 空路 + degraded(vector_timeout), BM25 兜底
- recall anchor 选池: corpus 传对, 语料池空模块 → 空 rerank + degraded

Mock 边界 = retrieve_vector(真实 COS) / _load_blocks, monkeypatch 替换; 不碰真实 COS。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import asyncio

import pytest

from core.rag import assistant
from core.rag import query as rag_core

# 语料: 两模块块(ai-tutoring 完善文档 + rag-project 代码), 验证 corpus 过滤
BLOCKS = [
    {"text": "防套答案: 第1次要答案拦下给思路, count+1; 第2次才放行完整答案",
     "summary": "防作弊答案出口机制",
     "tags": {"module": "ai-tutoring", "section": "04", "source": "完善文档",
              "authority": 1.0, "file": "04-安全与防作弊", "file_path": "4.完善文档/04-安全与防作弊.md",
              "anchor": "04-安全与防作弊"}},
    {"text": "RAG 多路召回: 向量 + BM25 双路, RRF 融合 × authority 权威度 × 节锚定加权",
     "summary": "RAG 多路召回机制",
     "tags": {"module": "rag-system", "section": "", "source": "代码",
              "authority": 0.8, "file": "rag-query", "file_path": "3.代码/rag-query.md",
              "anchor": "rag-query"}},
]


class TestSelectCorpus:
    """select_corpus: 模块 anchor 过滤语料池"""

    def test_anchor_filters_module(self):
        pool = rag_core.select_corpus(BLOCKS, "ai-tutoring")
        assert len(pool) == 1
        assert pool[0]["tags"]["module"] == "ai-tutoring"

        pool = rag_core.select_corpus(BLOCKS, "rag-system")
        assert len(pool) == 1
        assert pool[0]["tags"]["module"] == "rag-system"

    def test_anchor_none_full_corpus(self):
        assert rag_core.select_corpus(BLOCKS, None) == BLOCKS

    def test_anchor_invalid_full_corpus(self):
        """非闭集 anchor → 全池(向后兼容)"""
        assert rag_core.select_corpus(BLOCKS, "bad-module") == BLOCKS

    def test_anchor_no_corpus_empty_pool(self):
        """闭集内但无语料模块(knowledge-graph) → 空池(范围门低置信兜底)"""
        assert rag_core.select_corpus(BLOCKS, "knowledge-graph") == []


class TestOrchestrateCorpus:
    """orchestrate corpus 参数: 先过滤再融合, 锚定公式不变"""

    def test_corpus_filters_pool(self):
        """传 corpus=ai-tutoring → 只返回该模块块, 不吐 rag-project"""
        strategy = {"locked_sections": [], "strategy": "retrieve"}
        vec = {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "distance": 0.1},
                        {"key": "ai-tutoring/rag-query/rag-query#0", "distance": 0.2}],
               "confidence": 0.9}
        bm = {"hits": [{"key": h["key"], "bm25_score": 8.0} for h in vec["hits"]], "confidence": 0.8}
        hits = rag_core.orchestrate("防套答案", BLOCKS, vec, bm, strategy,
                                    top_k=5, corpus="ai-tutoring")
        assert hits
        assert all(h["file_path"].startswith("4.完善文档") for h in hits)  # 只留 ai-tutoring 完善文档块

    def test_corpus_anchor_weight_unchanged(self):
        """锚定公式原样: 锁 04 节 → 04 块加权 1.5 仍排第一(corpus 不影响节级加权)"""
        strategy = {"locked_sections": ["04"], "strategy": "retrieve"}
        vec = {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "distance": 0.1}],
               "confidence": 0.9}
        bm = {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "bm25_score": 8.0}],
              "confidence": 0.8}
        hits = rag_core.orchestrate("防套答案", BLOCKS, vec, bm, strategy,
                                    top_k=5, corpus="ai-tutoring")
        assert hits[0]["section"] == "04"  # 节级锚定加权仍生效

    def test_corpus_empty_pool_no_hit(self):
        """corpus 指无语料模块 → 空 rerank(范围门低置信入口)"""
        strategy = {"locked_sections": [], "strategy": "retrieve"}
        vec = {"hits": [], "confidence": 0.0}
        bm = {"hits": [], "confidence": 0.0}
        hits = rag_core.orchestrate("知识图谱问题", BLOCKS, vec, bm, strategy,
                                    top_k=5, corpus="knowledge-graph")
        assert hits == []


class TestRecall:
    """assistant.recall 双路编排: 超时降级 + anchor 选池 + degraded"""

    @pytest.fixture(autouse=True)
    def stub_load(self, monkeypatch):
        monkeypatch.setattr(rag_core, "_load_blocks", lambda: BLOCKS)

    def test_recall_both_hits_no_degraded(self, monkeypatch):
        """两路都命中 → rerank 有内容, 无 degraded"""
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0",
                                                  "distance": 0.1}], "confidence": 0.9})
        r = asyncio.run(assistant.recall("防套答案", anchor="ai-tutoring"))
        assert r["rerank"]
        assert r["degraded"] == []

    def test_recall_vector_timeout_degrade(self, monkeypatch):
        """向量路超时(阻塞 3s > 2s) → 空路 + degraded(vector_timeout), BM25 兜底"""

        def slow(*a, **k):
            import time
            time.sleep(3)
            return {"hits": [{"key": "k", "distance": 0.1}], "confidence": 0.9}

        monkeypatch.setattr(rag_core, "retrieve_vector", slow)
        r = asyncio.run(assistant.recall("防套答案", anchor="ai-tutoring"))
        assert assistant.DEGRADED_VECTOR in r["degraded"]
        assert not r["vec"]["hits"]        # 空路
        assert r["rerank"]                  # BM25 仍兜底有命中

    def test_recall_vector_exception_degrade(self, monkeypatch):
        """向量路异常 → 空路 + degraded"""

        def boom(*a, **k):
            raise RuntimeError("cos down")

        monkeypatch.setattr(rag_core, "retrieve_vector", boom)
        r = asyncio.run(assistant.recall("防套答案", anchor="ai-tutoring"))
        assert assistant.DEGRADED_VECTOR in r["degraded"]
        assert not r["vec"]["hits"]

    def test_recall_anchor_empty_corpus_degrade(self, monkeypatch):
        """anchor 指无语料模块 → 空 rerank + degraded(bm25_empty), 无生成"""
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0",
                                                  "distance": 0.1}], "confidence": 0.9})
        r = asyncio.run(assistant.recall("知识图谱问题", anchor="knowledge-graph"))
        assert r["rerank"] == []            # 语料池空 → 范围门低置信入口
        assert assistant.DEGRADED_BM25 in r["degraded"]  # BM25 空

    def test_recall_corpus_passed_to_orchestrate(self, monkeypatch):
        """anchor 闭集 → corpus 传对, 只该模块块进 rerank"""
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0",
                                                  "distance": 0.1}], "confidence": 0.9})
        r = asyncio.run(assistant.recall("防套答案", anchor="ai-tutoring"))
        assert r["corpus"] == "ai-tutoring"
        assert all("4.完善文档" in h["file_path"] for h in r["rerank"])

    def test_recall_no_anchor_full_pool(self, monkeypatch):
        """anchor None → corpus=None 全池(向后兼容)"""
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q: {"hits": [{"key": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0",
                                                  "distance": 0.1}], "confidence": 0.9})
        r = asyncio.run(assistant.recall("防套答案", anchor=None))
        assert r["corpus"] is None
        assert r["rerank"]
