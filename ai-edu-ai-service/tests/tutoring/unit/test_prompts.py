"""
任务 4: 提示词工厂 core/tutoring/prompts.py 测试

覆盖:
- 4.1 decide 决策器系统提示词(闭集+语义、hint/approach 反例、exercise_complete 联动、
      current_question 权威、终止 vs 澄清、安全 flag、snapshot label 注入)
- 4.2 generate 分类型生成规约(六类齐全、hint 禁数值、approach 无最终答案等)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)


HISTORY = [
    {"role": "user", "content": "鸡兔同笼，共35头94脚，各几只？"},
    {"role": "ai", "content": "先找题目里的已知条件，你能列出来吗？"},
    {"role": "user", "content": "设鸡有x只"},
]


class TestDecidePrompt:
    """4.1 decide 决策器提示词"""

    def _prompt(self, **overrides):
        from core.tutoring.prompts import build_decide_prompt

        kwargs = dict(
            history=HISTORY,
            snapshot_labels=["二元一次方程组", "一元一次方程"],
            subject_hint="math",
        )
        kwargs.update(overrides)
        return build_decide_prompt(**kwargs)

    def test_snapshot_labels_injected(self):
        """掌握度快照 label 候选注入 prompt(接地)"""
        prompt = self._prompt()
        assert "二元一次方程组" in prompt
        assert "一元一次方程" in prompt

    def test_type_closed_set_in_prompt(self):
        """六个动作类型都在提示词里"""
        prompt = self._prompt()
        for t in ["hint", "approach", "reveal", "concept", "switch", "end"]:
            assert f'"{t}"' in prompt

    def test_exercise_complete_linkage(self):
        """exercise_complete=true 必须 type=end + COMPLETED"""
        prompt = self._prompt()
        assert "exercise_complete" in prompt
        assert "COMPLETED" in prompt
        assert "end" in prompt

    def test_hint_approach_examples(self):
        """hint 与 approach 各给了一个具体例子(反例拆开)"""
        prompt = self._prompt()
        assert "设" in prompt  # hint 反问例子(设哪个未知数)
        assert "大纲" in prompt or "步骤" in prompt  # approach 思路大纲

    def test_end_vs_concept_distinction(self):
        """终止型无关 vs 澄清型模糊 区分"""
        prompt = self._prompt()
        assert "concept" in prompt
        assert "不终止" in prompt  # 澄清不终止会话
        assert "闲聊" in prompt or "无关" in prompt  # 无关 → end

    def test_first_message_not_switch_in_prompt(self):
        """B1 修复: 首条消息(无老师回复)不能输出 switch 的规则必须在 prompt 中"""
        prompt = self._prompt(history=[{"role": "user", "content": "测试题"}])
        assert "首条消息" in prompt
        assert "不能是 \"switch\"" in prompt or "绝不能是" in prompt
        assert "会话开始" in prompt

    def test_safety_flag_in_prompt(self):
        """安全 flag 检测在提示词里"""
        prompt = self._prompt()
        assert "safety_flag" in prompt

    def test_history_question_injected(self):
        """历史中的题目注入 prompt(当前题目从 history 推断,非后端传入)"""
        prompt = self._prompt()
        assert "鸡兔同笼，共35头94脚，各几只？" in prompt

    def test_current_question_inference_rule(self):
        """prompt 含'从历史推断当前题目'判定规则(贴新题→switch)"""
        prompt = self._prompt()
        assert "当前题目判定" in prompt
        assert "switch" in prompt

    def test_history_formatted(self):
        """对话历史被格式化进 prompt"""
        prompt = self._prompt()
        assert "设鸡有x只" in prompt


class TestGenerationRules:
    """4.2 generate 分类型生成规约"""

    def _rule(self, action_type):
        from core.tutoring.prompts import GENERATION_RULES

        return GENERATION_RULES[action_type]

    def test_all_six_types_covered(self):
        """六种动作类型各有生成规约"""
        from core.tutoring.prompts import GENERATION_RULES

        assert set(GENERATION_RULES.keys()) == {
            "hint", "approach", "reveal", "concept", "switch", "end",
        }

    def test_hint_forbids_numbers_and_steps(self):
        """hint: 零步骤、不含数值"""
        rule = self._rule("hint")
        assert "零步骤" in rule or "一个" in rule or "1 条" in rule or "一条" in rule
        assert "数值" in rule or "答案" in rule

    def test_approach_no_final_answer(self):
        """approach: 思路大纲、不含最终数值答案"""
        rule = self._rule("approach")
        assert "大纲" in rule or "步骤" in rule
        assert "数值" in rule or "答案" in rule

    def test_reveal_full_solution(self):
        """reveal: 完整解答"""
        rule = self._rule("reveal")
        assert "完整" in rule or "解答" in rule

    def test_generate_prompt_embeds_rule(self):
        """build_generate_prompt 把对应规约嵌入 prompt"""
        from core.tutoring.prompts import build_generate_prompt

        prompt = build_generate_prompt(
            action_type="hint",
            history=HISTORY,
        )
        from core.tutoring.prompts import GENERATION_RULES
        assert GENERATION_RULES["hint"] in prompt
