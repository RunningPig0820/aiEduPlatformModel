"""
上下文组装与模型路由

- truncate_history: 历史截断(保留最近 ~12 条;当前题目由 history 推断,Java 零题目状态)
- snapshot_top_n: 掌握度快照 top-N(防体积撑爆窗口;薄弱知识点优先)
- get_decide_llm / get_generate_llm: decide/generate 按配置独立取模型

对齐: openspec/changes/ai-tutoring/design.md 决策 6(模型配对)/10(无状态与上下文压缩)
"""
from typing import Optional

from config.settings import settings
from core.gateway.factory import LLMFactory

DEFAULT_MAX_HISTORY = 12
DEFAULT_SNAPSHOT_TOP_N = 10


def truncate_history(history, max_turns: int = DEFAULT_MAX_HISTORY):
    """保留最近 max_turns 条对话历史(兼容 list[dict] / list[BaseModel])"""
    if not history:
        return []
    return list(history)[-max_turns:]


def _mastery_level(item) -> int:
    """取快照条目掌握度(兼容 dict / BaseModel)"""
    if hasattr(item, "mastery_level"):
        return item.mastery_level or 0
    return (item.get("mastery_level") or 0) if isinstance(item, dict) else 0


def snapshot_top_n(snapshot, top_n: int = DEFAULT_SNAPSHOT_TOP_N):
    """掌握度快照取 top-N。

    按掌握度升序排列(薄弱知识点在前),让模型优先关注薄弱点;
    同时限制快照体积,避免撑爆上下文窗口。
    """
    if not snapshot:
        return []
    items = list(snapshot)
    items.sort(key=_mastery_level)
    return items[:top_n]


def get_decide_llm():
    """decide 决策模型(判断密集,按 TUTORING_DECIDE_* 配置)"""
    return LLMFactory.create(
        settings.TUTORING_DECIDE_PROVIDER,
        settings.TUTORING_DECIDE_MODEL,
        temperature=settings.TUTORING_DECIDE_TEMPERATURE,
    )


def get_generate_llm():
    """generate 生成模型(内容生成,按 TUTORING_GENERATE_* 配置)"""
    return LLMFactory.create(
        settings.TUTORING_GENERATE_PROVIDER,
        settings.TUTORING_GENERATE_MODEL,
        temperature=settings.TUTORING_GENERATE_TEMPERATURE,
    )
