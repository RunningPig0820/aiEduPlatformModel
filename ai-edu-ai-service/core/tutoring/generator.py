"""
生成器 - generate 流式正文

按已放行的 action_type 渲染生成规约 → 原始方舟流式(保留思考模式)→ 事件流:
  meta(已放行 type)→ thinking*(真实推理)→ token(正文流)→ done(model_used)
中段抛错向上传播,由 API 层转成 event: error(参考 api/chat.py SSE 模式)。

说明: langchain 流式会丢弃 reasoning_content,故直连方舟读原始 SSE(见 ark_stream),
     thinking 事件用于前端展示"思考过程"(与 token 平行的内容流)。

对齐: openspec/changes/ai-tutoring/design.md 决策 2(类型先行流式)
     + tutoring-thinking-display(thinking 事件)
"""
import logging
from typing import Iterator, Optional

from config.settings import settings
from models.tutoring import GenerateRequest
from core.tutoring import ark_stream
from core.tutoring.context import truncate_history
from core.tutoring.prompts import build_generate_messages

logger = logging.getLogger(__name__)

# 空流兜底话术: 模型零 token(网络/服务抖动)时给固定引导,避免学生收到空回复
_EMPTY_STREAM_FALLBACK = "我这边刚才有点卡顿，我们换个角度：你先说说，从题目里你读到了哪些关键条件？"


def iter_tokens(request: GenerateRequest, streamer=None) -> Iterator[dict]:
    """按已放行 action_type 生成正文,产出事件 dict(API 层格式化为 SSE)。

    Args:
        request: Java 放行后传来的 GenerateRequest
        streamer: 注入用(测试);默认直连方舟 stream_chat(保留思考模式)

    Yields:
        {"event": "meta", "data": {"action_type": ...}}
        {"event": "thinking", "data": {"content": <推理分片>}}   # 可多条
        {"event": "token", "data": {"content": ...}}
        {"event": "done", "data": {"model_used": "provider/model"}}
    """
    streamer = streamer or ark_stream.stream_chat

    history = truncate_history(request.history)
    messages = build_generate_messages(
        action_type=request.action_type.value,
        history=history,
        subject_hint=request.subject_hint,
    )
    logger.debug("generate messages built (action=%s, n=%d)", request.action_type.value, len(messages))

    # meta 先行: 护栏已放行的 type,前端据此渲染
    yield {"event": "meta", "data": {"action_type": request.action_type.value}}

    conn = ark_stream.doubao_conn(
        settings.TUTORING_GENERATE_MODEL, settings.TUTORING_GENERATE_TEMPERATURE,
    )
    token_count = 0
    for delta in streamer(**conn, messages=ark_stream.messages_to_openai(messages)):
        if delta.get("reasoning"):
            yield {"event": "thinking", "data": {"content": delta["reasoning"]}}
        content = delta.get("content")
        if content:
            token_count += 1
            yield {"event": "token", "data": {"content": content}}

    # 空流兜底: 零 token 时给固定引导话术,避免学生收到空回复(Java 零 token 不落库)
    if token_count == 0:
        logger.warning("generate: 空流(0 token),给兜底话术")
        yield {"event": "token", "data": {"content": _EMPTY_STREAM_FALLBACK}}

    model_used = f"{settings.TUTORING_GENERATE_PROVIDER}/{settings.TUTORING_GENERATE_MODEL}"
    yield {"event": "done", "data": {"model_used": model_used}}
