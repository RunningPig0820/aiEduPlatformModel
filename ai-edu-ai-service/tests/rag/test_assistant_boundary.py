"""
A9 范围门低置信过滤测试 - assistant.check_boundary

覆盖(tasks E 组"boundary 低置信测试: 无语料模块拒答" + A9 子项):
- 空 rerank(无语料模块) → boundary(唯一拒答路径, C1)
- 低置信(综合分 <0.75 普通块 / <0.5 权威文档块) → boundary
- 高置信通过 → None(继续 generate)
- 权威文档块阈值 0.5: 0.6 通过 / 0.4 拒答
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


def _rerank_block(score, file_path="4.完善文档/04-安全与防作弊.md"):
    return [{"block_id": "b1", "title": "t", "summary": "s", "file_path": file_path,
             "score": score}]


class TestCheckBoundary:
    def test_empty_rerank_boundary(self):
        """空 rerank(无语料模块) → boundary 拒答(唯一拒答路径)"""
        ev = assistant.check_boundary([])
        assert ev is not None
        assert ev["reason"] == assistant.BOUNDARY_REASON == "low_confidence"
        assert ev["message"] == assistant.BOUNDARY_MSG

    def test_high_confidence_pass(self):
        """综合分 ≥阈值 → None(通过范围门, 继续 generate)"""
        assert assistant.check_boundary(_rerank_block(0.9)) is None

    def test_low_confidence_index_boundary(self):
        """普通块(非完善文档)综合分 <0.75 → boundary"""
        ev = assistant.check_boundary(_rerank_block(0.6, file_path="1.语雀/答疑理念.md"))
        assert ev is not None

    def test_index_threshold_boundary_exact(self):
        """普通块综合分 0.74(<0.75) → boundary; 0.75 → 通过"""
        assert assistant.check_boundary(
            _rerank_block(0.74, file_path="1.语雀/答疑理念.md")) is not None
        assert assistant.check_boundary(
            _rerank_block(0.75, file_path="1.语雀/答疑理念.md")) is None

    def test_authoritative_document_threshold_05(self):
        """完善文档块阈值 0.5: 0.4 拒答, 0.6 通过(权威文档放宽容差)"""
        assert assistant.check_boundary(_rerank_block(0.4)) is not None
        assert assistant.check_boundary(_rerank_block(0.6)) is None

    def test_boundary_contract(self):
        """boundary 事件结构: {message, reason}"""
        ev = assistant.check_boundary([])
        assert set(("message", "reason")) <= set(ev)
        assert ev["reason"] == "low_confidence"

    def test_no_generate_token_implied(self):
        """boundary 触发 → 话术固定写死(0 token, 不调 LLM)"""
        ev = assistant.check_boundary([])
        # 话术是常量非 LLM 生成
        assert ev["message"] == "未找到关联文档，我尚未掌握。"
