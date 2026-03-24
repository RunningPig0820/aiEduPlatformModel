"""
聊天相关的数据模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SceneEnum(str, Enum):
    """场景枚举 - 用户只能选择这些预定义场景"""
    PAGE_ASSISTANT = "page_assistant"
    HOMEWORK_GRADING = "homework_grading"
    FAQ = "faq"
    IMAGE_ANALYSIS = "image_analysis"
    CONTENT_GENERATION = "content_generation"
    MATH_TUTOR = "math_tutor"  # 数学辅导场景 -> 使用 qwen-math-turbo


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="角色: user, assistant, system")
    content: str = Field(..., description="消息内容")


class ToolCall(BaseModel):
    """工具调用"""
    id: str = Field(..., description="工具调用 ID")
    name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ChatRequest(BaseModel):
    """聊天请求 - 来自 Java 后端

    安全设计：
    - 用户可指定 provider + model，但必须在白名单内
    - 不指定则使用默认模型
    """
    message: str = Field(..., description="用户消息", max_length=10000)
    scene: Optional[str] = Field(None, description="场景代码（可选）")
    user_id: int = Field(..., description="用户 ID")
    session_id: Optional[str] = Field(None, description="会话 ID")
    page_code: Optional[str] = Field(None, description="页面编码")
    # 用户可指定的模型（必须在白名单内）
    provider: Optional[str] = Field(None, description="指定 Provider")
    model: Optional[str] = Field(None, description="指定模型名称")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")


class UsageInfo(BaseModel):
    """Token 使用信息"""
    prompt_tokens: int = Field(default=0, description="输入 token 数")
    completion_tokens: int = Field(default=0, description="输出 token 数")
    total_tokens: int = Field(default=0, description="总 token 数")


class ChatResponse(BaseModel):
    """聊天响应 - 返回给 Java 后端"""
    response: str = Field(..., description="AI 响应内容")
    session_id: str = Field(..., description="会话 ID")
    model_used: str = Field(..., description="使用的模型: provider/model")
    usage: Optional[UsageInfo] = Field(None, description="Token 使用信息")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="工具调用列表")


class StreamChunk(BaseModel):
    """流式响应块"""
    content: Optional[str] = Field(None, description="内容片段")
    model_used: Optional[str] = Field(None, description="使用的模型")
    usage: Optional[UsageInfo] = Field(None, description="Token 使用信息")
    tool_call: Optional[ToolCall] = Field(None, description="工具调用")
    finish_reason: Optional[str] = Field(None, description="结束原因")
    error: Optional[str] = Field(None, description="错误信息")