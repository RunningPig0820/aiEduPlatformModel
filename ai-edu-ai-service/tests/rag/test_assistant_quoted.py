"""
A6 is_quoted 确定性引用测试 - assistant.lcs_quote_match

覆盖(tasks E 组"is_quoted 纯函数测试: 命中/改写未命中/8字窗口"):
- 命中: answer 含块原文连续 ≥8 中文字符 → quoted 含该块
- 改写未命中: answer 全部改写、无连续 8 字命中 → 不含
- 8 字窗口边界: 恰好 8 字命中 → quoted; 7 字 → 不 quoted
- 英文窗口: 12 英文命中 → quoted; 11 英文 → 不 quoted
- 多块: 只 quoted 命中的块, 未命中块排除
- block_id 透传: quoted 返回块 id

纯函数, 无 LLM/COS, 直接测。
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

from core.rag import assistant

TEXT_A = "防套答案: 第1次要答案拦下给思路, count+1; 第2次才放行完整答案"
TEXT_B = "AI答疑面向小学到高中全学段, 启发式教学, 不直接给答案"

BLOCKS = [
    {"block_id": "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0", "text": TEXT_A},
    {"block_id": "ai-tutoring/语雀-答疑理念/答疑理念#0", "text": TEXT_B},
]


class TestLcsQuoteMatch:
    def test_hit_exact_text(self):
        """answer 含块原文连续 ≥8 中文字符 → quoted"""
        answer = "这个机制的思路是「第1次要答案拦下给思路」, 然后 count+1"
        quoted = assistant.lcs_quote_match(answer, BLOCKS)
        assert "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0" in quoted

    def test_rewrite_no_hit(self):
        """answer 全部改写、无连续 8 字命中 → 不含该块"""
        answer = "关于防作弊, 系统会在首次请求时先引导思路, 累计后再开放完整内容"
        quoted = assistant.lcs_quote_match(answer, BLOCKS)
        assert quoted == []  # 无连续 8 字原样命中

    def test_other_block_not_quoted(self):
        """answer 命中 A 块 → 只 quoted A, B 块不误报"""
        answer = "防套答案: 第1次要答案拦下给思路"
        quoted = assistant.lcs_quote_match(answer, BLOCKS)
        assert "ai-tutoring/04-安全与防作弊/04-安全与防作弊#0" in quoted
        assert "ai-tutoring/语雀-答疑理念/答疑理念#0" not in quoted

    def test_window_8_cn_boundary(self):
        """恰好 8 中文字符命中 → quoted"""
        blk = [{"block_id": "b1", "text": "甲乙丙丁戊己庚辛壬癸"}]
        assert assistant.lcs_quote_match("他说：甲乙丙丁戊己庚辛，之后继续", blk) == ["b1"]

    def test_window_7_cn_no(self):
        """7 中文字符 → 不 quoted(窗口不足)"""
        blk = [{"block_id": "b1", "text": "甲乙丙丁戊己庚辛壬癸"}]
        assert assistant.lcs_quote_match("他说：甲乙丙丁戊己庚，之后继续", blk) == []

    def test_window_12_en_hit(self):
        """12 英文字符 → quoted"""
        blk = [{"block_id": "b1", "text": "The quick brown fox jumps over"}]
        answer = "原理是 The quick brown fox jumps 这一段"
        assert assistant.lcs_quote_match(answer, blk) == ["b1"]

    def test_window_11_en_no(self):
        """11 英文 → 不 quoted(11×0.667=7.33 < 8)"""
        blk = [{"block_id": "b1", "text": "ABCDEFGHIJKLMNOP"}]
        answer = "前缀 ABCDEFGHIJK 出现"  # 连续 11 英文
        assert assistant.lcs_quote_match(answer, blk) == []

    def test_window_12_en_hit_precise(self):
        """12 英文 → quoted(12×0.667=8.0 ≥ 8)"""
        blk = [{"block_id": "b1", "text": "ABCDEFGHIJKLMNOP"}]
        answer = "前缀 ABCDEFGHIJKL 出现"  # 连续 12 英文
        assert assistant.lcs_quote_match(answer, blk) == ["b1"]

    def test_empty_answer(self):
        """空 answer → 无 quoted"""
        assert assistant.lcs_quote_match("", BLOCKS) == []

    def test_no_blocks(self):
        assert assistant.lcs_quote_match("任意内容", []) == []
