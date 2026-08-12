"""
方舟(Ark)原始 SSE 流式客户端 - 保留豆包思考模式并透传推理内容

背景: langchain-openai 的 ChatOpenAI 流式解析会**丢弃 reasoning_content**
(实测 additional_kwargs 也为空),无法把思考过程展示给前端。故 decide/generate
的流式主路径改为**直连方舟 OpenAI 兼容接口**读原始 SSE:

- 请求体带 `thinking: {"type": "enabled"}`(显式开思考,与默认一致但更确定)
- 流式 delta 同时可能含 `reasoning_content`(→ thinking 事件)、`content`(→ token 事件)、
  `tool_calls`(→ decide function-calling 的 ActionMeta 参数,按 index 累积)

测试: tests/tutoring/unit/test_ark_stream.py(_parse_sse_lines 为纯函数,可离线测)
"""
import json
import logging
from typing import Any, Dict, Iterable, Iterator, List, Optional

import httpx
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from config.settings import settings
from core.gateway.factory import LLMFactory
from models.tutoring import ActionMeta

logger = logging.getLogger(__name__)


def _parse_sse_lines(lines: Iterable[str]) -> Iterator[Dict[str, Any]]:
    """从原始 SSE 行序列提取 delta dict(纯函数,可离线测试)。

    每行格式: 'data: {json}' 或 'data: [DONE]'。
    yield 结构固定:
        {"reasoning": str|None, "content": str|None, "tool_calls": list|None}
    非 2xx 之外的流内错误(顶层 error / finish_reason=="error")抛 RuntimeError,
    由调用方降级或透传 error 事件。
    """
    for line in lines:
        if not line or not line.startswith("data:"):
            continue
        data = line[len("data:"):].strip()
        if data == "[DONE]":
            return
        try:
            obj = json.loads(data)
        except json.JSONDecodeError:
            logger.warning("ark_stream: 跳过无法解析的 SSE 行: %r", line[:120])
            continue

        if "error" in obj:
            raise RuntimeError(f"ark stream error: {json.dumps(obj['error'], ensure_ascii=False)[:200]}")

        choices = obj.get("choices") or []
        if not choices:
            continue
        choice = choices[0]
        if choice.get("finish_reason") == "error":
            raise RuntimeError("ark stream finish_reason=error")

        delta = choice.get("delta") or {}
        tool_calls: Optional[List[Dict[str, Any]]] = None
        if delta.get("tool_calls"):
            tool_calls = []
            for tc in delta["tool_calls"]:
                fn = tc.get("function") or {}
                tool_calls.append({
                    "index": tc.get("index", 0),
                    "name": fn.get("name"),
                    "arguments": fn.get("arguments", "") or "",
                })
        yield {
            "reasoning": delta.get("reasoning_content"),
            "content": delta.get("content"),
            "tool_calls": tool_calls,
        }


def stream_chat(
    *,
    model: str,
    api_key: str,
    api_base: str,
    temperature: float,
    messages: List[dict],
    tools: Optional[List[dict]] = None,
    timeout: float = 120.0,
) -> Iterator[Dict[str, Any]]:
    """直连方舟 chat/completions 流式读取(OpenAI 兼容)。

    Args:
        model: 方舟模型 ID(如 doubao-seed-2-0-lite-260428)
        api_key / api_base: 方舟凭据与接入点
        temperature: 采样温度
        messages: OpenAI 格式消息(见 messages_to_openai)
        tools: OpenAI 格式工具列表(decide 的 ActionMeta function tool)

    Yields:
        _parse_sse_lines 的 delta dict(reasoning/content/tool_calls)
    Raises:
        RuntimeError: HTTP 非 2xx 或流内错误(调用方降级/透传)
    """
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        # 显式开思考: 保证 reasoning_content 流式返回(与默认一致,更确定)
        "thinking": {"type": "enabled"},
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    with httpx.stream(
        "POST",
        f"{api_base}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    ) as resp:
        if resp.status_code != 200:
            body = resp.read().decode("utf-8", "replace")
            raise RuntimeError(f"ark stream http {resp.status_code}: {body[:200]}")
        yield from _parse_sse_lines(resp.iter_lines())


def messages_to_openai(messages: List[BaseMessage]) -> List[dict]:
    """LangChain 消息列表 → OpenAI 格式(支持多模态)。

    HumanMessage 的 content 列表(text/image_url)已是 OpenAI 多模态格式,直接透传;
    SystemMessage/AIMessage 的 content 为字符串。
    """
    out: List[dict] = []
    for m in messages:
        if isinstance(m, SystemMessage):
            role = "system"
        elif isinstance(m, AIMessage):
            role = "assistant"
        else:
            role = "user"
        out.append({"role": role, "content": m.content})
    return out


def action_meta_tool() -> dict:
    """ActionMeta → OpenAI function tool(decide function-calling 用)。

    用 Pydantic 原生 JSON Schema(含 $defs)直传方舟,实测可用(R1 spike: 200 +
    完整 tool args + Pydantic 校验通过)。若个别模型拒绝,structured.py 的
    JSON mode 降级路径兜底。
    """
    return {
        "type": "function",
        "function": {
            "name": "ActionMeta",
            "description": "输出一次答疑交互的决策元数据(ActionMeta)",
            "parameters": ActionMeta.model_json_schema(),
        },
    }


def doubao_conn(model: str, temperature: float) -> dict:
    """方舟连接参数(与 LLMFactory._create_doubao 单一来源对齐)。"""
    return {
        "model": model,
        "api_key": settings.DOUBAO_API_KEY,
        "api_base": LLMFactory.PROVIDER_CONFIGS["doubao"]["api_base"],
        "temperature": temperature,
    }
