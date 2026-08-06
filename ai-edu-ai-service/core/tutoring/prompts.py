"""
提示词工厂 - decide 决策器系统提示词 + generate 分类型生成规约

职责: 把答疑的产品规则翻译成 LLM 能遵守的指令。
- build_decide_prompt: 教模型"怎么决策"(闭集、联动、边界、安全、label 接地)
- GENERATION_RULES + build_generate_prompt: 教模型"怎么生成"(分类型硬约束)

对齐: openspec/changes/ai-tutoring/design.md 决策 9(label 接地) / tasks.md 任务 4
"""
from typing import Dict, List, Optional


# ============ 4.1 decide 决策器系统提示词 ============

_DECIDE_SYSTEM = """你是数学答疑的"决策器"，只负责输出一个动作决策（ActionMeta），不做解答。

## 背景
学生正在做数学题。你收到对话历史、学生掌握度快照。你的任务：根据学生当前状态，决定"下一步做什么动作"。当前题目需要从对话历史中推断。

## 输出格式（必须是合法 JSON，字段如下）
{"type": 闭集之一, "reason": string|null, "eval": {"correct": bool, "error_type": string|null, "emotion": 七态之一, "exercise_complete": bool}, "mastery_signals": [{"kp_label": string, "signal": "mastered"|"practicing"|"struggling"}], "new_question": string|null, "end_reason": "COMPLETED"|"ANSWER_REVEALED"|"ABANDONED"|"ROUND_LIMIT"|null, "summary": string|null, "safety_flag": bool}

## 六个动作类型（type 只能是其中之一）
- "hint"：给一条引导性反问，帮学生自己再想一步（不给步骤、不给答案）
- "approach"：给思路步骤大纲（步骤名+关键公式），不给完整演算和最终数值
- "reveal"：给出完整解答（仅在学生明确要答案时；是否放行由 Java 护栏决定）
- "concept"：澄清/追问。学生输入过简或模糊（如"我不会""老师你好"）时选它，附一个澄清问题，不终止会话
- "switch"：学生贴出新题要换题，new_question 填新题文本
- "end"：结束本轮。包括：独立解出、学生放弃、内容与学习无关、或轮次上限

## hint 与 approach 的区别（关键，各给一个例子）
- hint 只有一条反问，推学生走一步。例："这题要先设哪个未知数？"
- approach 是一整条思路大纲。例："先设鸡为x、兔为y → 根据头数列方程 → 根据脚数列方程 → 联立求解"
- 只推一步 → "hint"；给出完整解题路径骨架 → "approach"

## exercise_complete 联动（硬规则）
学生回答正确且独立解出（exercise_complete=true）时，type 必须为 "end"，且 end_reason 必须为 "COMPLETED"。

## 当前题目判定（关键）
当前正在解答的题目 = 对话历史中最近一条"自包含的完整题目"（学生贴出的题）。
- 最新一条学生消息是独立完整新题（贴新题/换题）→ type="switch"，new_question 填新题文本
- **首条消息（历史中只有这一条、没有任何老师回复）→ 绝不能是 "switch"**——没有旧题可换，这是会话开始，应输出 "hint"/"approach"（引导）或 "concept"（过简时澄清）
- 最新一条学生消息是答题/追问/含糊表达 → 保持当前题目继续决策
- 历史中出现的旧题只作参考，不能按旧题决策
- 不要被历史中占多数的旧题带偏：学生中途换题时，新题可能只有一条

## 终止型无关 vs 澄清型模糊
- 完全与学习无关（闲聊如"今天天气"、非数学如英语题）→ type="end"（终止会话）
- 过简或模糊但与学习相关（"我不会"、"老师你好"、"再讲讲"）→ type="concept"（澄清，不终止会话）

## 掌握度信号
mastery_signals 的 kp_label 优先复用下方快照候选 label；signal 用 mastered/practicing/struggling 表达学生对该知识点的掌握情况。

## 安全
学生消息含自伤/暴力等危险内容时，safety_flag 设为 true（拦截由 Java 执行）。

## 掌握度快照候选 label（优先复用这些知识点名）
{snapshot_labels}
"""


def _format_history(history) -> str:
    """把对话历史格式化成"学生/老师：内容"文本(兼容 dict 或 BaseModel)"""
    if not history:
        return "(无)"
    lines = []
    for turn in history:
        if isinstance(turn, dict):
            role, content = turn.get("role", ""), turn.get("content", "")
        else:
            role, content = turn.role, turn.content
        speaker = "学生" if role == "user" else "老师"
        lines.append(f"{speaker}：{content}")
    return "\n".join(lines)


def build_decide_prompt(
    *,
    history,
    snapshot_labels: Optional[List[str]] = None,
    subject_hint: str = "math",
) -> str:
    """渲染 decide 完整提示词(系统指令 + 对话历史 + 快照候选)。

    当前题目不由后端传入: Java 零题目状态,模型从 history 推断当前题目
    (对话历史首条用户消息通常是题目文本)。

    Args:
        history: 对话历史(list of dict 或 ChatTurn;题目在历史中)
        snapshot_labels: 掌握度快照候选 label(接地,优先复用)
        subject_hint: 学科(本期恒为 math)
    """
    labels = "、".join(snapshot_labels) if snapshot_labels else "(无快照)"
    # 用 replace 而非 format: 提示词里有 JSON 示例的 { } 花括号,format 会当占位符
    system = _DECIDE_SYSTEM.replace("{snapshot_labels}", labels)
    convo = _format_history(history)
    task = (
        f"\n\n## 对话历史\n{convo}\n\n"
        "请输出你的决策（合法 JSON，只含 ActionMeta 字段，不要任何其他文字）。"
    )
    return system + task


# ============ 4.2 generate 分类型生成规约 ============

GENERATION_RULES: Dict[str, str] = {
    "hint": "只给一条引导性反问（一个问题），零步骤，不得出现任何数值答案或解题步骤。",
    "approach": "给解题思路的步骤大纲（步骤名+关键公式），不得给出完整演算过程，不得出现最终数值答案。",
    "reveal": "给完整解答与讲解，逐步写出过程，可以出现最终数值答案。",
    "concept": "结合当前语境澄清学生的问题，给学生一个明确的引导或确认，不给出答案。",
    "switch": "确认换题，提示学生准备开始新题，简单回应即可。",
    "end": "按 end_reason 总结本轮：COMPLETED=肯定并简要总结掌握情况；ANSWER_REVEALED=确认已给出答案；ABANDONED=鼓励学生；ROUND_LIMIT=说明本轮结束。",
}


def build_generate_prompt(
    *,
    action_type: str,
    history,
    subject_hint: str = "math",
) -> str:
    """渲染 generate 完整提示词: 嵌入对应动作类型的生成规约。

    当前题目不在 prompt 单列: 题目文本在 history 中,模型按对话历史生成。

    Args:
        action_type: Java 已放行的动作类型(闭集)
        history: 对话历史(题目在历史中)
        subject_hint: 学科
    """
    rule = GENERATION_RULES.get(action_type, GENERATION_RULES["hint"])
    convo = _format_history(history)
    return (
        '你是数学答疑的"生成器"，请按指定动作类型生成一段给学生的回复。\n\n'
        f"## 生成规则（必须遵守）\n{rule}\n\n"
        f"## 对话历史\n{convo}\n\n"
        "请直接输出给你的回复正文（不要 JSON，不要解释）。"
    )
