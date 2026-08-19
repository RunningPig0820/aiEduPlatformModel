"""
决策器 - decide 单次调用 + 流式决策(思考展示)

- decide(): 非流式,组装上下文 → structured 四段降级 → ActionMeta(降级兜底路径)
- iter_decide_events(): 流式,直连方舟读原始 SSE,边吐 thinking 事件(豆包真实推理)
  边收集 function-calling 的 tool args → ActionMeta;原始流失败时降级到 decide()

对齐: openspec/changes/ai-tutoring/design.md 决策 2/7
     + tutoring-thinking-display(thinking 事件,保留思考模式)
"""
import json
import logging

from config.settings import settings
from models.tutoring import ActionMeta, ActionType, DecideRequest, EndReason, Eval
from core.tutoring import ark_stream
from core.tutoring.context import truncate_history, snapshot_top_n, get_decide_llm
from core.tutoring.prompts import build_decide_messages
from core.tutoring.structured import _extract_json, _normalize_emotion, generate_action_meta

logger = logging.getLogger(__name__)


def _sanitize_end_consistency(meta: ActionMeta) -> ActionMeta:
    """保证 type=end 与 end_reason/eval 联动一致(确定性护栏,不信任模型格式)。

    实测 doubao「断言答对但答案错误」场景: reason 明说"不应收尾/继续引导"却输出
    type=end,且 end_reason 偶发 null / COMPLETED / ANSWER_REVEALED 与 correct=false 矛盾
    (java 会真收尾,答错的学生被"恭喜";summary 还可能泄出完整解答)。end 联动契约:
    - COMPLETED 必须 correct=true 且 exercise_complete=true(独立解出)
    - end_reason 缺失 → 无效 end
    无效 end → 降级 type=concept(生成规约允许"明确引导/确认、拉回题目、不给答案",
    可告知"答案不对"),清掉 end 字段,保持会话 ACTIVE、不终止。
    """
    if meta.type != ActionType.END:
        return meta
    invalid = (
        meta.end_reason is None
        or (
            meta.end_reason == EndReason.COMPLETED
            and not (meta.eval.correct and meta.eval.exercise_complete)
        )
    )
    if not invalid:
        return meta
    logger.warning(
        "decide: type=end 但 end 联动不一致(end_reason=%s, correct=%s, exercise_complete=%s) → 降级 concept 保持会话",
        meta.end_reason, meta.eval.correct, meta.eval.exercise_complete,
    )
    meta.type = ActionType.CONCEPT
    meta.end_reason = None
    meta.summary = None
    return meta


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

    return _sanitize_end_consistency(generate_action_meta(llm, messages))


def iter_decide_events(request: DecideRequest, streamer=None, llm=None):
    """流式决策: 保留豆包思考模式,边吐 thinking 事件(真实推理)边收集决策,绝不抛异常。

    主路径(直连方舟,见 ark_stream): 原始 SSE 流里 reasoning_content → thinking 事件;
    tool_calls 按 index 累积 → ActionMeta。原始流失败/args 非法 → 降级 decide()
    (非流式四段管线,该次无 thinking 展示,罕见)。

    Yields:
        {"event": "thinking", "data": {"content": str}}  # 思考分片(可多条)
        {"event": "meta", "data": ActionMeta}             # 收尾,唯一
    换题信号短路: 只 yield meta(type=switch),无 thinking。
    """
    # Java 换题信号: 本轮新增了题目 → 短路 switch(不调 LLM,不吐思考)
    if request.is_new_question:
        logger.info("decide: Java 换题信号 is_new_question=true → 短路 type=switch")
        meta = ActionMeta(
            type=ActionType.SWITCH,
            reason="Java 检测到新题信号,短路换题",
            eval=Eval(correct=False),
        )
        yield {"event": "meta", "data": meta.model_dump(mode="json")}
        return

    streamer = streamer or ark_stream.stream_chat
    messages = build_decide_messages(
        history=truncate_history(request.history),
        snapshot_labels=[s.label for s in snapshot_top_n(request.mastery_snapshot)],
        subject_hint=request.subject_hint,
    )

    meta = None
    try:
        conn = ark_stream.doubao_conn(
            settings.TUTORING_DECIDE_MODEL, settings.TUTORING_DECIDE_TEMPERATURE,
        )
        acc = {}  # tool_call index → {"name", "arguments"}
        content_acc = ""
        for delta in streamer(
            **conn,
            messages=ark_stream.messages_to_openai(messages),
            tools=[ark_stream.action_meta_tool()],
        ):
            if delta.get("reasoning"):
                yield {"event": "thinking", "data": {"content": delta["reasoning"]}}
            if delta.get("content"):
                content_acc += delta["content"]
            for tc in (delta.get("tool_calls") or []):
                idx = tc.get("index", 0)
                prev = acc.get(idx, {"name": "", "arguments": ""})
                acc[idx] = {
                    "name": tc.get("name") or prev["name"],
                    "arguments": prev["arguments"] + (tc.get("arguments") or ""),
                }
        if acc:
            # 主路径: function-calling 返回 tool args
            args = json.loads(acc[0]["arguments"])
            meta = ActionMeta.model_validate(args)
            logger.info("decide: function-calling 流式成功 type=%s", meta.type.value)
        elif content_acc:
            # 兜底: 模型未走 tool_call、直接吐 ActionMeta JSON(实测 doubao 偶发)→ 直接解析
            obj = _extract_json(content_acc)
            if obj:
                # _normalize_emotion: 与 structured.py 一致,宽容中文/小写情绪值,
                # 避免 emotion 校验失败触发降级(丢失原始 reason/mastery_signals)
                meta = ActionMeta.model_validate(_normalize_emotion(json.loads(obj)))
                logger.info("decide: content JSON 流式解析成功 type=%s", meta.type.value)
    except Exception as e:
        logger.warning("decide: 原始流失败,降级非流式 decide(): %s", e)

    if meta is None:
        # 降级: 非流式四段管线(绝不抛异常);is_new_question 短路已被上面处理,这里正常路径
        meta = decide(request, llm)

    # 流式成功路径也过一致性护栏(decide() 内部已护栏,幂等)
    yield {"event": "meta", "data": _sanitize_end_consistency(meta).model_dump(mode="json")}
