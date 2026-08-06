"""
结构化输出保障 - 四段降级管线 (安全关键)

保证 decide 接口绝不返回畸形 ActionMeta:
① with_structured_output(function_calling)
② JSON mode
③ 正则提取 + Pydantic
④ 兜底 ActionMeta(type=hint)

对齐: openspec/changes/ai-tutoring/design.md 决策 5 / tasks.md 任务 3
冒烟结论(任务 1.3): deepseek-v4-flash function_calling ✅ / json_mode ✅,
故 ① 是默认路径,②③④ 是保险。
"""
import json
import logging
from typing import Optional

from models.tutoring import ActionMeta, ActionType, Eval, EmotionF7

logger = logging.getLogger(__name__)


def _fallback() -> ActionMeta:
    """④ 兜底: 温和提示,绝不泄答案、绝不阻塞"""
    logger.error("structured: 四段管线全部失败,返回兜底 type=hint")
    return ActionMeta(
        type=ActionType.HINT,
        reason="结构化输出四段降级兜底",
        eval=Eval(correct=False, emotion=EmotionF7.NEUTRAL),
        degraded=True,  # 兜底信号: Java 据此监控 Python 降级频次
    )


def _schema_instructions() -> str:
    """compact ActionMeta JSON schema 描述(用于纠错 prompt)"""
    return (
        'type: "hint"|"approach"|"reveal"|"concept"|"switch"|"end", '
        'reason: string|null, '
        'eval: {"correct": bool, "error_type": string|null, "emotion": '
        '"NEUTRAL"|"CONFUSED"|"FRUSTRATED"|"ANXIOUS"|"CONFIDENT"|"INTERESTED"|"BORED", '
        '"exercise_complete": bool}, '
        'mastery_signals: [{"kp_label": string, "signal": "mastered"|"practicing"|"struggling"}], '
        'new_question: string|null, '
        'end_reason: "COMPLETED"|"ANSWER_REVEALED"|"ABANDONED"|"ROUND_LIMIT"|null, '
        'summary: string|null, '
        'safety_flag: bool, '
        'degraded: bool(默认 false,仅兜底时 true)'
    )


def _corrective_prompt(bad_raw: str, error: str) -> str:
    """纠错 prompt: 只让模型修正 schema,不整段重生成(重试域约束)"""
    return (
        "你上次输出的 ActionMeta JSON 不合法。\n"
        f"你上次的输出: {bad_raw}\n"
        f"校验错误: {error}\n"
        "请只输出修正后的合法 JSON 对象(不要解释,不要任何其他文字)。字段要求:\n"
        f"{_schema_instructions()}"
    )


# json_object 模式要求 prompt 里出现 "json" 字样,顺带强化"只要 JSON"约束
_JSON_HINT = "\n\n(重要: 你的最终回答必须是一个合法 JSON 对象,不要包含任何其他文字。)"


def _extract_json(text: str) -> Optional[str]:
    """从混杂文本中提取第一个平衡的 JSON 对象(处理嵌套花括号与字符串内引号)"""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_str = False
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '"':
            if i > 0 and text[i - 1] != "\\":
                in_str = not in_str
        elif not in_str:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    return None


def _parse_and_validate(
    raw: str,
    correction_llm,
    corrective_retries: int,
    extract: bool = False,
) -> Optional[ActionMeta]:
    """解析 + Pydantic 校验,失败时发纠错 prompt(只修 schema)。

    重试域: 不重试 LLM 整段调用,只做有上限的 schema 纠错。
    返回 None 表示放弃本段,交给下一段。
    """
    for attempt in range(corrective_retries + 1):
        candidate = _extract_json(raw) if extract else raw
        if not candidate:
            error = "未找到 JSON 对象"
        else:
            try:
                data = json.loads(candidate)
            except json.JSONDecodeError as e:
                error = f"JSON 解析失败: {e}"
            else:
                try:
                    return ActionMeta.model_validate(data)
                except Exception as ve:
                    error = f"Pydantic 校验失败: {ve}"

        if attempt < corrective_retries and correction_llm is not None:
            logger.warning(
                "structured: 解析失败,纠错重试 %d/%d: %s",
                attempt + 1, corrective_retries, error,
            )
            try:
                raw = correction_llm.invoke(_corrective_prompt(raw, error)).content
            except Exception as ce:
                logger.warning("structured: 纠错调用失败: %s", ce)
                return None
        else:
            logger.warning("structured: 解析失败,放弃该段: %s", error)
            return None
    return None


def _try_function_calling(llm, prompt: str) -> Optional[ActionMeta]:
    """① function calling: bind_tools(ActionMeta) + 手动解析 tool_call

    不用 with_structured_output: langchain-openai 1.x 默认走 response_format=json_schema
    (Structured Outputs),deepseek 不支持(400);bind_tools 走原生 tool-calling,
    任务 1.3 冒烟已实测可用。tool_call args 交给 Pydantic 校验,不合法则降级。
    """
    try:
        llm_with_tool = llm.bind_tools([ActionMeta])
        msg = llm_with_tool.invoke(prompt)
        if not msg.tool_calls:
            logger.warning("structured: ①未返回 tool_call(content=%r)", getattr(msg, "content", None))
            return None
        args = msg.tool_calls[0].get("args") or {}
        return ActionMeta.model_validate(args)
    except Exception as e:
        logger.warning("structured: ①function_calling 失败: %s", e)
        return None


def _try_json_mode(llm, prompt: str, corrective_retries: int) -> Optional[ActionMeta]:
    """② JSON mode: response_format=json_object + 解析校验"""
    try:
        llm_json = llm.bind(response_format={"type": "json_object"})
        raw = llm_json.invoke(prompt + _JSON_HINT).content
    except Exception as e:
        logger.warning("structured: ②json_mode 调用失败: %s", e)
        return None
    if not raw:
        return None
    # 纠错复用 json mode 绑定的 llm,保证再输出也是 JSON
    return _parse_and_validate(raw, correction_llm=llm_json, corrective_retries=corrective_retries)


def _try_regex_extract(llm, prompt: str, corrective_retries: int) -> Optional[ActionMeta]:
    """③ 正则提取 + Pydantic"""
    try:
        raw = llm.invoke(prompt).content
    except Exception as e:
        logger.warning("structured: ③文本调用失败: %s", e)
        return None
    if not raw:
        return None
    return _parse_and_validate(raw, correction_llm=llm, corrective_retries=corrective_retries, extract=True)


def generate_action_meta(llm, prompt: str, corrective_retries: int = 1) -> ActionMeta:
    """四段降级管线,保证返回合法 ActionMeta(绝不抛异常、绝不吐畸形)。

    Args:
        llm: 已配置的 ChatModel(decide 用,配置驱动)
        prompt: 渲染好的 decide 提示词
        corrective_retries: schema 纠错重试次数(默认 1,有上限)
    """
    meta = _try_function_calling(llm, prompt)
    if meta is not None:
        return meta

    meta = _try_json_mode(llm, prompt, corrective_retries)
    if meta is not None:
        return meta

    meta = _try_regex_extract(llm, prompt, corrective_retries)
    if meta is not None:
        return meta

    return _fallback()
