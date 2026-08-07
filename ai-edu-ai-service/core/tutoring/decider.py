"""
决策器 - decide 单次调用

组装上下文(历史截断 + 快照 top-N)→ 渲染 decide prompt → structured 四段降级 → ActionMeta

对齐: openspec/changes/ai-tutoring/design.md 决策 2(交互模型)/7(单次调用,schema 可拆)
"""
import logging

from models.tutoring import ActionMeta, ActionType, DecideRequest, Eval
from core.tutoring.context import truncate_history, snapshot_top_n, get_decide_llm
from core.tutoring.prompts import build_decide_messages
from core.tutoring.structured import generate_action_meta

logger = logging.getLogger(__name__)


def decide(request: DecideRequest, llm=None) -> ActionMeta:
    """对一次 decide 请求做决策,返回 ActionMeta(绝不畸形,绝不抛异常)。

    换题信号短路: Java 检测到新题(新图/新题 URL)时置 request.is_new_question=true,
    Python 直接返回 type=switch,不调 LLM(确定性,100% 准,省调用)。
    —— 换题检测由 Java 做(它知道何时收到新图),Python 不再从 history 推断(无状态做不准)。

    Args:
        request: Java 传来的 DecideRequest(已过 Pydantic 校验)
        llm: 注入用(测试);默认按 TUTORING_DECIDE_* 配置创建
    """
    # Java 换题信号: 本轮新增了题目 → 短路 switch(不调 LLM)
    if request.is_new_question:
        logger.info("decide: Java 换题信号 is_new_question=true → 短路 type=switch")
        return ActionMeta(
            type=ActionType.SWITCH,
            reason="Java 检测到新题信号,短路换题",
            eval=Eval(correct=False),
        )

    llm = llm or get_decide_llm()

    history = truncate_history(request.history)
    snapshot = snapshot_top_n(request.mastery_snapshot)
    snapshot_labels = [s.label for s in snapshot] if snapshot else []

    messages = build_decide_messages(
        history=history,
        snapshot_labels=snapshot_labels,
        subject_hint=request.subject_hint,
    )
    logger.debug("decide messages built (n=%d)", len(messages))

    return generate_action_meta(llm, messages)
