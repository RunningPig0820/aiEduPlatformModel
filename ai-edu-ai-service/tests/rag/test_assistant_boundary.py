"""
A9 范围门低置信过滤测试 - assistant.check_boundary

覆盖(tasks E 组"boundary 低置信测试: 无语料模块拒答" + A9 子项):
- 空 rerank(无语料模块) → boundary(唯一拒答路径, C1)
- 双路置信度都低于阈值(vec<0.75 且 bm<0.5) → boundary
- 单路达阈值即通过(双路互补, 一路够用)
- boundary 事件结构: {message, reason=low_confidence}

纯逻辑, 直接测。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

from core.rag import assistant

# rerank 非空占位(前端契约块, 含 score 但不参与判定)
RERANK_HIT = [{"block_id": "b1", "title": "t", "summary": "s",
               "file_path": "4.完善文档/04-安全与防作弊.md", "score": 0.03}]


class TestCheckBoundary:
    def test_empty_rerank_boundary(self):
        """空 rerank(无语料模块) → boundary 拒答(唯一拒答路径)"""
        ev = assistant.check_boundary([])
        assert ev is not None
        assert ev["reason"] == assistant.BOUNDARY_REASON == "low_confidence"
        assert ev["message"] == assistant.BOUNDARY_MSG

    def test_both_low_boundary(self):
        """双路置信度都低于阈值 → boundary"""
        ev = assistant.check_boundary(RERANK_HIT, vec_conf=0.4, bm_conf=0.3)
        assert ev is not None
        assert ev["reason"] == "low_confidence"

    def test_vec_high_pass(self):
        """向量路 ≥0.75 → 通过(即使 BM25 低)"""
        assert assistant.check_boundary(RERANK_HIT, vec_conf=0.75, bm_conf=0.0) is None

    def test_bm_high_pass(self):
        """BM25 路 ≥0.5 → 通过(即使向量低)"""
        assert assistant.check_boundary(RERANK_HIT, vec_conf=0.0, bm_conf=0.5) is None

    def test_both_high_pass(self):
        """双路都高 → 通过"""
        assert assistant.check_boundary(RERANK_HIT, vec_conf=0.9, bm_conf=0.8) is None

    def test_boundary_threshold_exact(self):
        """阈值边界: vec=0.75 过 / 0.74 拒(bm 低); bm=0.5 过 / 0.49 拒(vec 低)"""
        # 0.74 < 0.75 且 0.3 < 0.5 → 拒
        assert assistant.check_boundary(RERANK_HIT, vec_conf=0.74, bm_conf=0.3) is not None
        # 0.75 ≥ 0.75 → 过(单路够)
        assert assistant.check_boundary(RERANK_HIT, vec_conf=0.75, bm_conf=0.3) is None
        # 0.49 < 0.5 且 0.0 < 0.75 → 拒
        assert assistant.check_boundary(RERANK_HIT, vec_conf=0.0, bm_conf=0.49) is not None
        # 0.5 ≥ 0.5 → 过
        assert assistant.check_boundary(RERANK_HIT, vec_conf=0.0, bm_conf=0.5) is None

    def test_boundary_contract(self):
        """boundary 事件结构: {message, reason}"""
        ev = assistant.check_boundary([], vec_conf=0.0, bm_conf=0.0)
        assert set(("message", "reason")) <= set(ev)
        assert ev["reason"] == "low_confidence"

    def test_no_generate_token_implied(self):
        """boundary 触发 → 话术固定写死(0 token, 不调 LLM)"""
        ev = assistant.check_boundary([])
        assert ev["message"] == "未找到关联文档，我尚未掌握。"

    def test_default_conf_zero(self):
        """未传置信度(默认 0) → 非空 rerank 双路 0 都低 → 拒答"""
        # 注意: 这暴露了调用方必须传真实置信度; 默认 0 是保守拒答
        ev = assistant.check_boundary(RERANK_HIT)
        assert ev is not None
