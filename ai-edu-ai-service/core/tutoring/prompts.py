"""
提示词工厂 - decide 决策器系统提示词 + generate 分类型生成规约

职责: 把答疑的产品规则翻译成 LLM 能遵守的指令。
- build_decide_prompt / build_decide_messages: 教模型"怎么决策"
- GENERATION_RULES + build_generate_prompt / build_generate_messages: 教模型"怎么生成"

看图答疑(design 决策 14): 题目可能是图片(公式+图形)。带 image_url 的消息在文本中
渲染为 [图片题目] 占位,真实图通过多模态消息通道(HumanMessage 的 image_url)进入模型。
"""
from typing import Dict, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


# ============ 4.1 decide 决策器系统提示词 ============

_DECIDE_SYSTEM = """你是数学答疑的"决策器"，只负责输出一个动作决策（ActionMeta），不做解答。

## 背景
学生正在做数学题。你收到对话历史、学生掌握度快照。你的任务：根据学生当前状态，决定"下一步做什么动作"。当前题目需要从对话历史中推断（可能是文本，也可能是图片）。

## 看图（题目是图片时）
题目可能以图片给出（含公式、受力分析图、实例图、标注）。图片在对话历史中显示为 [图片题目]。
- 必须结合图片内容决策：图中的题目文字、公式、图形、标注都是题目的一部分
- 学生可能追问图中元素（如"图中这个力往哪"、"这个角是多少"），要能引用图作答
- 换题判定：最新一条学生消息是新的题目图片（贴新图）→ type="switch"

## 输出格式（必须是合法 JSON，字段如下）
{"type": 闭集之一, "reason": string|null, "question_kps": ["知识点", ...]|null, "eval": {"correct": bool, "error_type": string|null, "emotion": 七态之一, "exercise_complete": bool}, "mastery_signals": [{"topic_label": string, "signal": "mastered"|"practicing"|"struggling"}], "new_question": string|null, "end_reason": "COMPLETED"|"ANSWER_REVEALED"|"ABANDONED"|"ROUND_LIMIT"|null, "summary": string|null, "safety_flag": bool}

## question_kps（可选，不干扰主决策）
question_kps 为当前题目涉及的知识点（如 "二元一次方程组"、"假设法"）。读题时顺手列出即可，不确定可为 null，不要求每次必填。

## 六个动作类型（type 只能是其中之一）
- "hint"：给一条引导性反问，帮学生自己再想一步（不给步骤、不给答案）
- "approach"：给思路步骤大纲（步骤名+关键公式），不给完整演算和最终数值
- "reveal"：给出完整解答（**仅当学生明确表达要答案**，如"给答案""答案是多少""直接说答案"；是否放行由 Java 护栏决定）。**答错、答偏绝不触发 reveal**——答错是"作答"，走 hint/approach
- "concept"：澄清/追问/引导回题。一切"不在答题"的内容（闲聊、状态表达如"太热了"、过简模糊、非数学题）都用它——正常回应、接住学生，把话题拉回当前题目，**不终止会话**
- "switch"：学生贴出新题要换题（新题可能是文本或图片），new_question 填新题文本
- "end"：结束本轮（仅三类）：①独立解出（COMPLETED）②学生表达结束的意思非常明确（如"我不做了""结束吧""再见"；ABANDONED）③安全内容（Java 拦截）。**在答题的内容、不在答题但未明确结束的内容，绝不归 end**——那是"引导解题"或"引导回题"，走 hint/approach/concept

## hint 与 approach 的区别（关键，各给一个例子）
- hint 只有一条反问，推学生走一步。例："这题要先设哪个未知数？"
- approach 是一整条思路大纲。例："先设鸡为x、兔为y → 根据头数列方程 → 根据脚数列方程 → 联立求解"
- 只推一步 → "hint"；给出完整解题路径骨架 → "approach"
- **先想一步原则：默认 "hint"，只有学生明确求助/卡住（"我不会""太难了""给个思路"）才升 "approach"**。不要一上来就把完整解题路径交给学生，先让学生自己动脑
- **作答时同此原则**：答错/答偏默认 "hint"（只推一步，让学生再想一步）；学生卡住/明确求助才升 "approach"（思路大纲）；答对但未独立解出 → "approach"（续推思路，不给最终数值）

## exercise_complete 联动（硬规则）
学生回答正确且独立解出（exercise_complete=true）时，type 必须为 "end"，且 end_reason 必须为 "COMPLETED"。

## 当前题目判定（关键）
当前正在解答的题目 = 对话历史中最近一条"自包含的完整题目"（学生贴出的题，文本或图片）。
- 最新一条学生消息是独立完整新题（贴新题/换题，文本或图片）→ type="switch"，new_question 填新题文本
- **首条消息（历史中只有这一条、没有任何老师回复）→ 绝不能是 "switch"**——没有旧题可换，这是会话开始，**默认输出 "hint"**（一条引导性反问，零步骤零答案）；仅当学生首条就明确求助（"我不会""太难了""给个思路"）才可 "approach" 或 "concept"（过简时澄清）。**"approach"（完整步骤大纲）绝不作首条消息的默认选择**
- 最新一条学生消息是答题/追问/含糊表达 → 保持当前题目继续决策
- 历史中出现的旧题只作参考，不能按旧题决策
- 不要被历史中占多数的旧题带偏：学生中途换题时，新题可能只有一条

## 核心判定：是否在答题（两分法，不做精细意图解读）
无法确定学生每句话的确切意图（是想结束、是闲聊、还是抱怨状态），只判断"这句话和当前答题是否相关"：
- **在答题**（作答/答错/答偏/求助/提问/追问——"我不会""太难了""给个思路"也是求助，算在答题；无论对错、是否跑偏）→ 引导解题，绝不 end、绝不 reveal：
  - 答错/答偏 → type="hint"（只推一步，先想一步原则）；学生明确卡住/求助 → type="approach"（思路大纲），eval.correct=false，可填 error_type
  - 答对但未独立解出 → type="approach"（续推思路，不给最终数值）
  - **否定硬规则：任何在答题的内容（无论对错、是否跑偏）绝不输出 type="end"、绝不输出 type="reveal"**——答错 ≠ 无关，答错 ≠ 要答案
- **不在答题**（闲聊、状态表达如"太热了""累了"、离题、纯打招呼如"老师你好"、非数学题、以及一切无法确定的话）→ 一律引导回答题：type="concept"（正常回应、接住学生、把话题拉回当前题目），保持会话 ACTIVE，**绝不 end**；非数学题说明只辅导数学并引导回来
- **唯一例外：只有学生表达结束的意思非常明确（"我不做了""结束吧""再见"）才 type="end"(ABANDONED)**；无法确定时默认引导回答题，宁可不 end

## 答对判定与收尾（正确性只看数值，不看语气；答对必须确认收尾）
- **判对前必须代入验算（不可凭直觉/语气）**：学生给出数值答案，先把数值代回题目算一遍再判对错。例：题"小明10岁、妈妈38岁，几年后妈妈年龄是小明2倍"，学生答"18年" → 验算 38+18=56、10+18=28、56=2×28 ✓ 判对；答"20年" → 验算 38+20=58、10+20=30、58≠2×30 ✗ 判错。**验算过程在 reason 里写出来**
- **疑问/不确定措辞也算作答，正确性按数值判断，不看语气**：学生用问句给出答案（「是18吗」「是18年吗」「答案是不是18」「18对不对」）同样是"作答"。数值正确 → eval.correct=true，**绝不要因为"语气不确定/用问句"就把正确数值判错**、继续 hint
- **学生独立给出正确数值（含用问句确认）＝ 独立解出**：exercise_complete=true，type="end"，end_reason="COMPLETED"，summary 肯定并确认收尾——不要因"是问句"就回到 hint 引导循环
- **学生说「我刚刚答案是对的」「我是不是做对了」「快告诉我对不对」→ 是"要求确认/复核"，不是闲聊、不是引导回题**：核对学生之前给出的答案——
  - 之前答案**正确** → eval.correct=true，exercise_complete=true，type="end"（COMPLETED），确认答对并收尾
  - 之前答案**错误** → eval.correct=false，**明确告知"答案不对"**并指出错因，继续引导（默认 hint 只推一步，卡住/求助才 approach），绝不 end

## 掌握度信号（题型粒度，不是知识点）
mastery_signals 记录学生对**题型**的掌握度，不是知识点：
- topic_label = 题型名（如 "鸡兔同笼"、"相遇问题"、"牛吃草"）
- 不要输出知识点名（如 "二元一次方程组"、"假设法"）——知识点由后端根据题型派生
- signal 用 mastered/practicing/struggling 表达学生对该题型的掌握情况
- 题型名要稳定规范：同一题型在不同学生/会话里输出一致的名字，别随意换说法（"鸡兔同笼" 不要写成 "鸡兔同笼问题"）；用最常见、最短的题型名

## 安全
学生消息含自伤/暴力等危险内容时，safety_flag 设为 true（拦截由 Java 执行）。

## 学生题型掌握度快照（背景参考：学生练得好的题型；仅作上下文提示，不照抄为 mastery_signals 的 topic_label）
{snapshot_labels}
"""


def _format_history(history) -> str:
    """把对话历史格式化成"学生/老师：内容"文本(兼容 dict 或 BaseModel)。

    带 image_url 的消息渲染成 [图片题目] 占位——真实图走多模态消息通道(不进文本)。
    """
    if not history:
        return "(无)"
    lines = []
    for turn in history:
        if isinstance(turn, dict):
            role, content = turn.get("role", ""), turn.get("content", "")
            image_url = turn.get("image_url")
        else:
            role, content = turn.role, turn.content
            image_url = getattr(turn, "image_url", None)
        speaker = "学生" if role == "user" else "老师"
        if image_url:
            lines.append(f"{speaker}：[图片题目]")
        elif content:
            lines.append(f"{speaker}：{content}")
        else:
            lines.append(f"{speaker}：(空)")
    return "\n".join(lines)


def _find_question_image_url(history) -> Optional[str]:
    """取对话历史中最近一条带 image_url 的消息(当前题目图;换题=新图进来)"""
    for turn in reversed(history or []):
        url = turn.get("image_url") if isinstance(turn, dict) else getattr(turn, "image_url", None)
        if url:
            return url
    return None


def _decide_system(snapshot_labels: Optional[List[str]]) -> str:
    labels = "、".join(snapshot_labels) if snapshot_labels else "(无快照)"
    # 用 replace 而非 format: 提示词里有 JSON 示例的 { } 花括号,format 会当占位符
    return _DECIDE_SYSTEM.replace("{snapshot_labels}", labels)


def _decide_task_text() -> str:
    return "\n\n请输出你的决策（合法 JSON，只含 ActionMeta 字段，不要任何其他文字）。"


def build_decide_prompt(
    *,
    history,
    snapshot_labels: Optional[List[str]] = None,
    subject_hint: str = "math",
) -> str:
    """渲染 decide 完整提示词(系统指令 + 对话历史 + 快照候选)。

    纯文本通道(向后兼容)。图片题目用 build_decide_messages。
    """
    system = _decide_system(snapshot_labels)
    convo = _format_history(history)
    return system + f"\n\n## 对话历史\n{convo}\n\n" + _decide_task_text()


def build_decide_messages(
    *,
    history,
    snapshot_labels: Optional[List[str]] = None,
    subject_hint: str = "math",
) -> List[BaseMessage]:
    """渲染 decide 多模态消息列表(图+文通道,看图答疑)。

    无图时退回纯文本 HumanMessage(行为与 build_decide_prompt 一致);
    有图时 HumanMessage 带 image_url,真实题目图进模型。
    """
    system = _decide_system(snapshot_labels)
    convo = _format_history(history)
    image_url = _find_question_image_url(history)
    text_content = f"## 对话历史\n{convo}\n\n" + _decide_task_text()

    messages: List[BaseMessage] = [SystemMessage(content=system)]
    if image_url:
        messages.append(HumanMessage(content=[
            {"type": "text", "text": text_content},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]))
    else:
        messages.append(HumanMessage(content=text_content))
    return messages


# ============ 4.2 generate 分类型生成规约 ============

GENERATION_RULES: Dict[str, str] = {
    "hint": "只给一条引导性反问（一个问题），零步骤，不得出现任何数值答案或解题步骤。",
    "approach": "给解题思路的步骤大纲（步骤名+关键公式），不得给出完整演算过程，不得出现最终数值答案。",
    "reveal": "给完整解答与讲解，逐步写出过程，可以出现最终数值答案。",
    "concept": "结合当前语境接住学生（澄清模糊输入、回应与学习无关的闲聊），给学生一个明确的引导或确认，把话题拉回当前题目，不给出答案。",
    "switch": "确认换题，提示学生准备开始新题，简单回应即可。",
    "end": "只按 end_reason 说明原因/鼓励，禁止写入完整解答或最终数值：COMPLETED=肯定掌握情况并简要总结；ANSWER_REVEALED=确认已给出答案（不复述答案）；ABANDONED=鼓励学生；ROUND_LIMIT=说明本轮结束。",
}


def _generate_system(action_type: str) -> str:
    rule = GENERATION_RULES.get(action_type, GENERATION_RULES["hint"])
    return (
        '你是数学答疑的"生成器"，请按指定动作类型生成一段给学生的回复。\n\n'
        f"## 生成规则（必须遵守）\n{rule}"
    )


def _generate_text_content(history) -> str:
    convo = _format_history(history)
    return f"## 对话历史\n{convo}\n\n请直接输出给你的回复正文（不要 JSON，不要解释）。"


def build_generate_prompt(
    *,
    action_type: str,
    history,
    subject_hint: str = "math",
) -> str:
    """渲染 generate 完整提示词(纯文本通道,向后兼容)。"""
    return _generate_system(action_type) + "\n\n" + _generate_text_content(history)


def build_generate_messages(
    *,
    action_type: str,
    history,
    subject_hint: str = "math",
) -> List[BaseMessage]:
    """渲染 generate 多模态消息列表(图+文通道,看图答疑)。"""
    image_url = _find_question_image_url(history)
    messages: List[BaseMessage] = [SystemMessage(content=_generate_system(action_type))]
    if image_url:
        messages.append(HumanMessage(content=[
            {"type": "text", "text": _generate_text_content(history)},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]))
    else:
        messages.append(HumanMessage(content=_generate_text_content(history)))
    return messages
