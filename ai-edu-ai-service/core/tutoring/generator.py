"""
生成器 - generate 流式正文

按已放行的 action_type 渲染生成规约 → llm.stream() → 事件流:
  meta(已放行 type)→ token(正文流)→ done(model_used)
中段抛错向上传播,由 API 层转成 event: error(参考 api/chat.py SSE 模式)。

对齐: openspec/changes/ai-tutoring/design.md 决策 2(类型先行流式)
"""
import logging
from typing import Iterator, Optional

from config.settings import settings
from models.tutoring import GenerateRequest
from core.tutoring.context import truncate_history, get_generate_llm
from core.tutoring.prompts import build_generate_messages

logger = logging.getLogger(__name__)

# 空流兜底话术: 模型零 token(网络/服务抖动)时给固定引导,避免学生收到空回复
_EMPTY_STREAM_FALLBACK = "我这边刚才有点卡顿，我们换个角度：你先说说，从题目里你读到了哪些关键条件？"


def iter_tokens(request: GenerateRequest, llm=None) -> Iterator[dict]:
    """按已放行 action_type 生成正文,产出事件 dict(API 层格式化为 SSE)。

    Args:
        request: Java 放行后传来的 GenerateRequest
        llm: 注入用(测试);默认按 TUTORING_GENERATE_* 配置创建

    Yields:
        {"event": "meta", "data": {"action_type": ...}}
        {"event": "token", "data": {"content": ...}}
        {"event": "done", "data": {"model_used": "provider/model"}}
    """
    llm = llm or get_generate_llm()

    history = truncate_history(request.history)
    messages = build_generate_messages(
        action_type=request.action_type.value,
        history=history,
        subject_hint=request.subject_hint,
    )
    logger.debug("generate messages built (action=%s, n=%d)", request.action_type.value, len(messages))

    # meta 先行: 护栏已放行的 type,前端据此渲染
    yield {"event": "meta", "data": {"action_type": request.action_type.value}}

    token_count = 0
    for chunk in llm.stream(messages):
        content = chunk.content
        if content:
            token_count += 1
            yield {"event": "token", "data": {"content": content}}

    # 空流兜底: 零 token 时给固定引导话术,避免学生收到空回复(Java 零 token 不落库)
    if token_count == 0:
        logger.warning("generate: 空流(0 token),给兜底话术")
        yield {"event": "token", "data": {"content": _EMPTY_STREAM_FALLBACK}}

    model_used = f"{settings.TUTORING_GENERATE_PROVIDER}/{settings.TUTORING_GENERATE_MODEL}"
    yield {"event": "done", "data": {"model_used": model_used}}
