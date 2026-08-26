"""
A4 rerank 精排 Top-K 测试 - assistant.rerank_blocks + recall 的 rerank 契约

覆盖(tasks E 组"rerank 精排 Top-K"):
- 只回传精排 Top-K(默认 3), 不吐全量
- 块结构 {block_id, title, summary, file_path, score}(前端契约, snake_case)
- title 取 anchor(或 file 兜底)
- recall 返回值: rerank(前端契约 3 块) + hits(orchestrate 完整含 text, generate 用)
- rerank 块数超过 top_k 截断

Mock 边界 = retrieve_vector(真实 COS), monkeypatch; 不碰真实 COS。
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

BLOCKS = [
    {"text": "防套答案: 第1次要答案拦下给思路, count+1; 第2次才放行完整答案",
     "summary": "防作弊答案出口机制",
     "tags": {"module": "ai-tutoring", "section": "04", "source": "完善文档",
              "authority": 1.0, "file": "04-安全与防作弊", "file_path": "4.完善文档/04-安全与防作弊.md",
              "anchor": "04-安全与防作弊", "pool": "slice"}},
    {"text": "流式输出用 SSE, 前端逐字展示, 性能优化减少卡顿",
     "summary": "流式与性能",
     "tags": {"module": "ai-tutoring", "section": "07", "source": "代码",
              "authority": 0.8, "file": "分析-09-流式", "file_path": "3.代码/分析-09-流式.md",
              "anchor": "流式", "pool": "slice"}},
    {"text": "AI答疑面向小学到高中全学段, 启发式教学",
     "summary": "AI答疑定位",
     "tags": {"module": "ai-tutoring", "section": "01", "source": "语雀",
              "authority": 0.7, "file": "语雀-答疑理念", "file_path": "1.语雀/答疑理念.md",
              "anchor": "答疑理念", "pool": "slice"}},
    {"text": "第四块, 超出默认 Top-K 应被截断",
     "summary": "多余块",
     "tags": {"module": "ai-tutoring", "section": "05", "source": "语雀",
              "authority": 0.5, "file": "语雀-多余", "file_path": "1.语雀/多余.md",
              "anchor": "多余", "pool": "slice"}},
]

# orchestrate 输出形状(含 text/authority 等完整字段)
HITS = [{
    "key": f"rag-slice/{b['tags']['file']}/{b['tags']['anchor']}#0",
    "score": round(1.0 - i * 0.1, 4),
    "authority": b["tags"]["authority"],
    "source": b["tags"]["source"],
    "section": b["tags"]["section"],
    "file": b["tags"]["file"],
    "file_path": b["tags"]["file_path"],
    "anchor": b["tags"]["anchor"],
    "summary": b["summary"],
    "text": b["text"],
} for i, b in enumerate(BLOCKS)]


class TestRerankBlocks:
    """rerank_blocks: 精排 Top-K + 前端契约结构"""

    def test_default_top_k_3(self):
        blocks = assistant.rerank_blocks(HITS)
        assert len(blocks) == assistant.RERANK_K == 3  # 默认只回传 3 块, 截断第 4 块

    def test_custom_top_k(self):
        blocks = assistant.rerank_blocks(HITS, top_k=2)
        assert len(blocks) == 2

    def test_contract_shape(self):
        """前端契约字段齐全: block_id/title/summary/file_path/score"""
        b = assistant.rerank_blocks(HITS)[0]
        assert set(("block_id", "title", "summary", "file_path", "score")) <= set(b)
        assert b["block_id"] == HITS[0]["key"]
        assert b["file_path"] == "4.完善文档/04-安全与防作弊.md"
        assert b["title"] == "04-安全与防作弊"      # title 取 anchor
        assert isinstance(b["score"], float)

    def test_title_fallback_file(self):
        """anchor 缺失 → title 取 file"""
        h = dict(HITS[0], anchor="")
        b = assistant.rerank_blocks([h])[0]
        assert b["title"] == "04-安全与防作弊"       # file 兜底

    def test_empty_hits_empty_blocks(self):
        assert assistant.rerank_blocks([]) == []

    def test_no_full_recall_text_not_in_rerank(self):
        """前端契约不吐 text/authority(不吐全量召回)"""
        b = assistant.rerank_blocks(HITS)[0]
        assert "text" not in b
        assert "authority" not in b


class TestRecallRerankContract:
    """recall 返回值: rerank(前端契约) + hits(完整含 text)"""

    @pytest.fixture(autouse=True)
    def stub_load(self, monkeypatch):
        monkeypatch.setattr(rag_core, "_load_all_blocks", lambda: BLOCKS)

    def test_recall_rerank_and_hits_split(self, monkeypatch):
        """rerank 前端契约(默认3块无text) + hits 完整(含text供generate)"""
        monkeypatch.setattr(rag_core, "retrieve_vector",
                            lambda q, vector_type="rag", module=None, categories=None: {"hits": [{"key": h["key"], "distance": 0.1} for h in HITS],
                                       "confidence": 0.9})
        r = asyncio.run(assistant.recall("防套答案", anchor="ai-tutoring"))
        assert len(r["rerank"]) == assistant.RERANK_K == 3     # 前端只回传 3 块
        assert "text" not in r["rerank"][0]                     # 不吐全量
        assert len(r["hits"]) == 4                              # 完整召回(含 text)留 generate
        assert "text" in r["hits"][0]
        # rerank 是 hits 的前 3 块映射
        assert r["rerank"][0]["block_id"] == r["hits"][0]["key"]
