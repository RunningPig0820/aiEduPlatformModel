"""
任务 4: 提示词工厂 core/tutoring/prompts.py 测试

覆盖:
- 4.1 decide 决策器系统提示词(闭集+语义、hint/approach 反例、exercise_complete 联动、
      current_question 权威、终止 vs 澄清、安全 flag、snapshot label 注入)
- 4.2 generate 分类型生成规约(六类齐全、hint 禁数值、approach 无最终答案等)
- 4.3 decide 两分法判定(在答题→引导/不在答题→concept引导回题)、end 收紧三类、reveal 门禁、end 不给答案
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
        """掌握度快照 label 注入 prompt(背景参考,不作 mastery_signals 题型名接地)"""
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
        """无关(闲聊)→ concept 继续(不终止),绝不被当成 end 收尾"""
        prompt = self._prompt()
        assert "concept" in prompt
        assert "不终止" in prompt  # 澄清不终止会话
        assert "闲聊" in prompt  # 无关 → concept 继续
        assert "绝不 end" in prompt  # 无关绝不归 end

    def test_answer_leads_to_guide_not_end(self):
        """作答答错/答偏 → hint/approach 引导、保持活跃，绝不 end/reveal（两分法"在答题"档）"""
        prompt = self._prompt()
        assert "作答" in prompt  # 两分法"在答题"档
        assert "eval.correct=false" in prompt  # 答错软信号
        assert "绝不输出 type=\"end\"" in prompt  # 否定硬规则: 绝不 end
        assert "绝不输出 type=\"reveal\"" in prompt  # 否定硬规则: 绝不 reveal
        assert "答对但未独立解出" in prompt  # 答对未解出 → approach 续推(不 end)

    def test_end_tightened_three_categories(self):
        """end 收紧三类 + 排除答错/答偏/求助/无关闲聊（作答与无关绝不归 end）"""
        prompt = self._prompt()
        assert "仅三类" in prompt  # end 收紧为三类
        assert "COMPLETED" in prompt  # 独立解出
        assert "ABANDONED" in prompt  # 主动明确表达结束
        assert "答错" in prompt and "答偏" in prompt and "求助" in prompt  # 排除项
        assert "无关" in prompt  # 无关闲聊同样不归 end
        assert "绝不归 end" in prompt

    def test_unrelated_maps_to_concept_keep_active(self):
        """不在答题(闲聊/太热了)→ concept 引导回题、保持 ACTIVE、绝不 end;仅明确结束才 end"""
        prompt = self._prompt()
        assert "无法确定" in prompt  # 两分法:不做精细意图解读
        assert "太热了" in prompt  # 状态表达正例(结束意图无法确定→不终止)
        assert "保持会话 ACTIVE" in prompt or "保持会话继续" in prompt  # 继续不终止
        assert "绝不 end" in prompt
        assert "我不做了" in prompt  # 明确结束正例 → 才 end(ABANDONED)

    def test_reveal_gated_on_explicit_ask(self):
        """reveal 门禁: 仅明确要答案触发，答错/答偏绝不触发"""
        prompt = self._prompt()
        assert "明确表达要答案" in prompt  # reveal 触发条件收紧
        assert "给答案" in prompt  # 明确要答案例子
        assert "绝不触发 reveal" in prompt  # 答错绝不 reveal

    def test_first_message_not_switch_in_prompt(self):
        """B1 修复: 首条消息(无老师回复)不能输出 switch 的规则必须在 prompt 中"""
        prompt = self._prompt(history=[{"role": "user", "content": "测试题"}])
        assert "首条消息" in prompt
        assert "不能是 \"switch\"" in prompt or "绝不能是" in prompt
        assert "会话开始" in prompt

    def test_first_message_defaults_to_hint(self):
        """B2 修复(2026-08): 首条消息默认 hint(引导反问),不默认 approach(完整步骤大纲)"""
        prompt = self._prompt(history=[{"role": "user", "content": "测试题"}])
        assert "默认输出" in prompt or "默认 \"hint\"" in prompt
        assert "绝不作" in prompt or "不作为首条消息的默认选择" in prompt
        assert "approach" in prompt
        assert "我不会" in prompt or "太难了" in prompt or "给个思路" in prompt  # 求助升 approach 触发词

    def test_think_one_step_first_in_prompt(self):
        """先想一步原则: hint 与 approach 区别处声明默认 hint、求助才 approach"""
        prompt = self._prompt()
        assert "先想一步原则" in prompt
        assert "只有学生明确求助" in prompt or "只有学生明确" in prompt
        assert "才升" in prompt or "才" in prompt

    def test_question_kps_in_prompt(self):
        """question_kps 字段 + 知识点语义指令在 decide prompt 中(前端知识点分析数据源)"""
        prompt = self._prompt()
        assert "question_kps" in prompt
        assert "知识点" in prompt

    def test_uncertain_tone_correct_answer(self):
        """答对判定: 疑问/不确定措辞(「是18吗」)也算作答,正确性看数值不看语气,绝不因问句判错"""
        prompt = self._prompt()
        assert "是18吗" in prompt  # 疑问语气正例
        assert "不看语气" in prompt  # 语气不确定 ≠ 判错
        assert "问句" in prompt

    def test_verify_by_substitution_required(self):
        """判对前必须代入验算: 把数值代回题目算一遍(例 38+18=56、56=2×28),不可凭直觉/语气"""
        prompt = self._prompt()
        assert "代入验算" in prompt
        assert "38+18" in prompt  # 验算正例
        assert "判错" in prompt  # 代入不成立 → 判错

    def test_correct_value_means_completed(self):
        """学生独立给出正确数值(含用问句确认)= 独立解出 → end COMPLETED,不回到 hint 循环"""
        prompt = self._prompt()
        assert "独立给出正确数值" in prompt
        assert "COMPLETED" in prompt
        assert "确认收尾" in prompt
        assert "hint 引导循环" not in prompt or "不要因" in prompt  # 显式否定回到 hint

    def test_assert_correct_is_confirmation_request(self):
        """学生断言答对(「我刚刚答案是对的」)→ 要求确认/复核,不是闲聊、不是引导回题"""
        prompt = self._prompt()
        assert "我刚刚答案是对的" in prompt
        assert "要求确认/复核" in prompt
        assert "不是引导回题" in prompt

    def test_assert_correct_verified_ends(self):
        """断言答对核实为对 → end COMPLETED 确认收尾"""
        prompt = self._prompt()
        assert "确认答对并收尾" in prompt

    def test_assert_correct_but_wrong_clear(self):
        """断言答对但实际错误 → 明确告知「答案不对」+ 继续引导,绝不 end"""
        prompt = self._prompt()
        assert "答案不对" in prompt  # 明确对错判断
        assert "继续引导" in prompt

    def test_mastery_signal_topic_semantics(self):
        """mastery_signals 输出题型语义: topic_label=题型名,不是知识点(题型化核心)"""
        prompt = self._prompt()
        assert "topic_label" in prompt
        assert "题型" in prompt
        assert "鸡兔同笼" in prompt  # 题型正例
        assert "不要输出知识点名" in prompt  # 反例:知识点交给后端派生

    def test_mastery_signal_topic_name_stable(self):
        """题型名稳定规范: 别换说法,用最常见最短的题型名"""
        prompt = self._prompt()
        assert "别随意换说法" in prompt
        assert "最常见" in prompt

    def test_mastery_signal_not_grounded_to_snapshot(self):
        """mastery_signals 不再接地快照候选(题型与知识点快照不同源)"""
        prompt = self._prompt()
        assert "优先复用" not in prompt  # 移除接地指令

    def test_question_kps_still_knowledge_point(self):
        """question_kps 仍输出知识点(不翻题型)"""
        prompt = self._prompt()
        assert "题目涉及的知识点" in prompt

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

    def test_end_rule_no_solution(self):
        """end 规约: 只说明原因/鼓励，禁止写入完整解答或最终数值（不给答案）"""
        rule = self._rule("end")
        assert "禁止写入完整解答或最终数值" in rule
        assert "鼓励" in rule  # 原因/鼓励语义
        # 不含"允许给答案"语义(reveal 才允许完整解答)
        assert "可以出现最终数值答案" not in rule

    def test_generate_prompt_embeds_rule(self):
        """build_generate_prompt 把对应规约嵌入 prompt"""
        from core.tutoring.prompts import build_generate_prompt

        prompt = build_generate_prompt(
            action_type="hint",
            history=HISTORY,
        )
        from core.tutoring.prompts import GENERATION_RULES
        assert GENERATION_RULES["hint"] in prompt


class TestImageMultimodal:
    """10.4/10.5 看图答疑: [图片题目]占位 + 多模态消息构建"""

    IMAGE_HISTORY = [
        {"role": "user", "content": "", "image_url": "https://cos-xxx/1.jpg"},
        {"role": "ai", "content": "先看图中物块的受力"},
    ]

    def test_image_placeholder_in_prompt(self):
        """带 image_url 的消息在文本 prompt 中渲染为 [图片题目] 占位"""
        from core.tutoring.prompts import build_decide_prompt

        prompt = build_decide_prompt(history=self.IMAGE_HISTORY)
        assert "[图片题目]" in prompt
        assert "1.jpg" not in prompt  # 真实 URL 不进文本(走多模态通道)

    def test_vision_instruction_in_prompt(self):
        """decide prompt 含看图决策指令"""
        from core.tutoring.prompts import build_decide_prompt

        prompt = build_decide_prompt(history=[{"role": "user", "content": "题"}])
        assert "看图" in prompt
        assert "图片" in prompt

    def test_decide_messages_with_image(self):
        """有图 → HumanMessage 含 text + image_url 两个 part"""
        from core.tutoring.prompts import build_decide_messages
        from langchain_core.messages import HumanMessage

        msgs = build_decide_messages(history=self.IMAGE_HISTORY)
        assert len(msgs) == 2
        human = msgs[1]
        assert isinstance(human, HumanMessage)
        parts = human.content
        assert any(p.get("type") == "image_url" and p["image_url"]["url"] == "https://cos-xxx/1.jpg"
                   for p in parts if isinstance(p, dict))
        assert any(p.get("type") == "text" and "[图片题目]" in p.get("text", "")
                   for p in parts if isinstance(p, dict))

    def test_decide_messages_text_only(self):
        """无图 → HumanMessage 是纯文本(向后兼容,无 image_url part)"""
        from core.tutoring.prompts import build_decide_messages
        from langchain_core.messages import HumanMessage

        msgs = build_decide_messages(history=[{"role": "user", "content": "鸡兔同笼"}])
        assert len(msgs) == 2
        assert isinstance(msgs[1], HumanMessage)
        assert isinstance(msgs[1].content, str)
        assert "鸡兔同笼" in msgs[1].content

    def test_find_latest_image(self):
        """当前题目图 = 历史中最近一条带 image_url 的消息(换题=新图)"""
        from core.tutoring.prompts import _find_question_image_url

        hist = [
            {"role": "user", "content": "", "image_url": "http://old.jpg"},
            {"role": "ai", "content": "..."},
            {"role": "user", "content": "", "image_url": "http://new.jpg"},
        ]
        assert _find_question_image_url(hist) == "http://new.jpg"

    def test_generate_messages_with_image(self):
        """generate 多模态消息: 有图 → HumanMessage 带 image_url"""
        from core.tutoring.prompts import build_generate_messages
        from langchain_core.messages import HumanMessage

        msgs = build_generate_messages(action_type="hint", history=self.IMAGE_HISTORY)
        assert len(msgs) == 2
        human = msgs[1]
        assert isinstance(human, HumanMessage)
        assert any(p.get("type") == "image_url" for p in human.content if isinstance(p, dict))
