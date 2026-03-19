"""
LLM API路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    emotion: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    大模型对话接口
    """
    # TODO: 实现LLM对话
    return ChatResponse(
        response="这是一个示例回复",
        session_id=request.session_id or "new-session",
        emotion="NEUTRAL"
    )


@router.post("/grade")
async def grade_homework(
    question: str,
    answer: str,
    student_answer: str
):
    """
    作业批改接口
    """
    # TODO: 实现AI批改
    return {
        "score": 85,
        "feedback": "批改反馈",
        "correct": True
    }