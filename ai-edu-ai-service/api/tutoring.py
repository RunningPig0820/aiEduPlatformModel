"""
AI 答疑 API 端点 - Java↔Python 内部调用(需 x-internal-token)

- POST /api/tutoring/decide    决策(非流式) → ActionMeta
- POST /api/tutoring/generate  生成(流式 SSE) → meta/token/done/error

对齐: openspec/changes/ai-tutoring/api.md + design.md 决策 2(decide → guard → generate)
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse

from api.chat import verify_internal_token
from models.tutoring import ActionMeta, DecideRequest, GenerateRequest
from core.tutoring.decider import decide
from core.tutoring.generator import iter_tokens

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutoring", tags=["Tutoring"])


@router.post("/decide", response_model=ActionMeta)
async def tutoring_decide(
    request: DecideRequest,
    x_internal_token: str = Header(None),
):
    """决策端点(非流式): 接收对话上下文,返回 ActionMeta。

    Java 每轮先调 decide → 护栏审批 type → 再调 generate。
    decide 可重试 1 次(纯函数),仍失败由 Java 对外兜底。
    """
    verify_internal_token(x_internal_token)
    try:
        return decide(request)
    except Exception as e:
        logger.error("decide failed: %s", e)
        raise HTTPException(status_code=500, detail="decide failed")


@router.post("/generate")
async def tutoring_generate(
    request: GenerateRequest,
    x_internal_token: str = Header(None),
):
    """生成端点(流式 SSE): 按已放行的 action_type 流式返回正文。

    类型先行: 先 event: meta(已放行 type)→ event: token(正文流)→ event: done。
    中段失败 → event: error,流终止(Java 不可重试,提示重发)。
    """
    verify_internal_token(x_internal_token)

    async def generate_stream():
        try:
            for ev in iter_tokens(request):
                data = json.dumps(ev["data"], ensure_ascii=False)
                yield f"event: {ev['event']}\ndata: {data}\n\n"
        except Exception as e:
            logger.error("generate failed: %s", e)
            error_data = json.dumps({"code": "500", "message": "生成失败"}, ensure_ascii=False)
            yield f"event: error\ndata: {error_data}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
