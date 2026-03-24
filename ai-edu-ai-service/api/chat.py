"""
对话 API 端点
"""
from fastapi import APIRouter, HTTPException, Header, Request
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncIterator
import json
import uuid
import logging

from models.chat import ChatRequest, ChatResponse, UsageInfo, StreamChunk
from core.gateway.router import ModelRouter
from config.settings import settings
from config.model_config import (
    MODEL_CONFIG,
    is_model_allowed,
    get_allowed_models,
    get_default_model_for_provider,
    get_global_default_model
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/llm", tags=["LLM"])


def verify_internal_token(x_internal_token: Optional[str] = Header(None)) -> str:
    """验证内部 Token"""
    if not x_internal_token:
        raise HTTPException(status_code=403, detail="Missing internal token")

    if x_internal_token != settings.INTERNAL_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid internal token")

    return x_internal_token


def validate_model(provider: Optional[str], model: Optional[str]) -> tuple:
    """
    验证模型是否在白名单内

    Args:
        provider: 用户指定的 provider
        model: 用户指定的 model

    Returns:
        (provider, model): 验证后的 provider 和 model

    Raises:
        HTTPException: 模型不在白名单内
    """
    # 未指定则使用全局默认模型（从配置读取）
    if not provider:
        return get_global_default_model()

    if not model:
        # 只指定了 provider，使用该 provider 的默认模型
        model = get_default_model_for_provider(provider)
        if not model:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider: {provider}"
            )

    # 白名单验证 - 从配置读取
    if not is_model_allowed(provider, model):
        allowed = get_allowed_models()
        allowed_list = [m["full_name"] for m in allowed]
        raise HTTPException(
            status_code=400,
            detail=f"Model '{provider}/{model}' not allowed. Allowed models: {allowed_list}"
        )

    return provider, model


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_internal_token: str = Header(None)
):
    """
    对话接口 - 仅供 Java 后端内部调用

    安全设计：
    - 用户可指定 provider + model，但必须在白名单内
    - 不指定则使用默认模型（glm-4-flash，免费）

    需要在 Header 中携带 x-internal-token
    """
    # 验证内部 Token
    verify_internal_token(x_internal_token)

    # 验证模型是否允许
    provider, model = validate_model(request.provider, request.model)

    try:
        # 创建 LLM
        llm, model_used = ModelRouter.create_llm(
            scene=request.scene,
            provider=provider,
            model=model
        )

        # 构建消息
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = []
        if request.context and "page_meta" in request.context:
            # 添加页面上下文
            page_meta = request.context["page_meta"]
            system_prompt = f"你是一个教育平台的 AI 助手。当前用户正在查看页面: {page_meta.get('title', '未知页面')}"
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=request.message))

        # 调用 LLM
        response = llm.invoke(messages)

        # 构建 session_id
        session_id = request.session_id or str(uuid.uuid4())

        # 构建 usage 信息
        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = UsageInfo(
                prompt_tokens=response.usage_metadata.get("input_tokens", 0),
                completion_tokens=response.usage_metadata.get("output_tokens", 0),
                total_tokens=response.usage_metadata.get("total_tokens", 0)
            )

        # 处理工具调用
        tool_calls = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                tool_calls.append({
                    "id": tc.get("id", ""),
                    "name": tc.get("name", ""),
                    "arguments": tc.get("args", {})
                })

        return ChatResponse(
            response=response.content or "",
            session_id=session_id,
            model_used=model_used,
            usage=usage,
            tool_calls=tool_calls
        )

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_internal_token: str = Header(None)
):
    """
    流式对话接口 - 仅供 Java 后端内部调用

    安全设计：
    - 用户可指定 provider + model，但必须在白名单内

    返回 SSE 格式的流式响应
    """
    # 验证内部 Token
    verify_internal_token(x_internal_token)

    # 验证模型是否允许
    provider, model = validate_model(request.provider, request.model)

    async def generate_stream() -> AsyncIterator[str]:
        try:
            # 创建 LLM
            llm, model_used = ModelRouter.create_llm(
                scene=request.scene,
                provider=provider,
                model=model
            )

            # 构建消息
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = []
            if request.context and "page_meta" in request.context:
                page_meta = request.context["page_meta"]
                system_prompt = f"你是一个教育平台的 AI 助手。当前用户正在查看页面: {page_meta.get('title', '未知页面')}"
                messages.append(SystemMessage(content=system_prompt))

            messages.append(HumanMessage(content=request.message))

            # 流式调用
            session_id = request.session_id or str(uuid.uuid4())
            total_tokens = 0

            for chunk in llm.stream(messages):
                if chunk.content:
                    # 发送内容块
                    data = json.dumps({"content": chunk.content}, ensure_ascii=False)
                    yield f"event: token\ndata: {data}\n\n"
                    total_tokens += 1

                # 处理工具调用
                if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        data = json.dumps({
                            "id": tc.get("id", ""),
                            "name": tc.get("name", ""),
                            "arguments": tc.get("args", {})
                        }, ensure_ascii=False)
                        yield f"event: tool_call\ndata: {data}\n\n"

            # 发送完成事件
            done_data = json.dumps({
                "model_used": model_used,
                "session_id": session_id,
                "usage": {"total_tokens": total_tokens}
            }, ensure_ascii=False)
            yield f"event: done\ndata: {done_data}\n\n"

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            error_data = json.dumps({"code": "400", "message": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            error_data = json.dumps({"code": "500", "message": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/allowed-models")
async def list_allowed_models(x_internal_token: str = Header(None)):
    """
    获取允许调用的模型列表 - 仅供 Java 后端内部调用

    用户只能从这个列表中选择模型
    """
    # 验证内部 Token
    verify_internal_token(x_internal_token)

    # 从配置读取允许的模型列表
    models = get_allowed_models()

    # 获取默认模型
    default_provider, default_model = get_global_default_model()

    return {
        "code": "00000",
        "message": "success",
        "data": {
            "allowed_models": models,
            "default_model": f"{default_provider}/{default_model}",
            "note": "调用时只能使用 allowed_models 中的模型"
        }
    }


@router.get("/models")
async def list_models(x_internal_token: str = Header(None)):
    """
    获取所有模型列表 - 仅供 Java 后端内部调用
    """
    # 验证内部 Token
    verify_internal_token(x_internal_token)

    from config.model_config import get_all_providers

    providers = get_all_providers()

    return {
        "code": "00000",
        "message": "success",
        "data": {
            "providers": providers
        }
    }


