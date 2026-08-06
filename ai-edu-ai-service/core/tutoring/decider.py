"""
决策器 - decide 单次调用

组装上下文(历史截断 + 快照 top-N)→ 渲染 decide prompt → structured 四段降级 → ActionMeta

对齐: openspec/changes/ai-tutoring/design.md 决策 2(交互模型)/7(单次调用,schema 可拆)
"""
import logging

from models.tutoring import ActionMeta, DecideRequest
from core.tutoring.context import truncate_history, snapshot_top_n, get_decide_llm
from core.tutoring.prompts import build_decide_prompt
from core.tutoring.structured import generate_action_meta

logger = logging.getLogger(__name__)


def decide(request: DecideRequest, llm=None) -> ActionMeta:
    """对一次 decide 请求做决策,返回 ActionMeta(绝不畸形,绝不抛异常)。

    Args:
        request: Java 传来的 DecideRequest(已过 Pydantic 校验)
        llm: 注入用(测试);默认按 TUTORING_DECIDE_* 配置创建
    """
    llm = llm or get_decide_llm()

    history = truncate_history(request.history)
    snapshot = snapshot_top_n(request.mastery_snapshot)
    snapshot_labels = [s.label for s in snapshot] if snapshot else []

    prompt = build_decide_prompt(
        history=history,
        snapshot_labels=snapshot_labels,
        subject_hint=request.subject_hint,
    )
    logger.debug("decide prompt(head): %s", prompt[:200])

    return generate_action_meta(llm, prompt)
