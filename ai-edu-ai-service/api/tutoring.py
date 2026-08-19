"""
AI 答疑 API 端点 - Java↔Python 内部调用(需 x-internal-token)

- POST /api/tutoring/decide    决策(流式 SSE) → agent 阶段事件 + meta(ActionMeta) + done
- POST /api/tutoring/generate  生成(流式 SSE) → meta/token/done/error

对齐: openspec/changes/tutoring-agent-protocol/api.md(decide 流式契约 + agent 事件)
     + ai-tutoring design.md 决策 2(decide → guard → generate)
"""
import json
import logging

from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse

from config.settings import settings
from api.chat import verify_internal_token
from models.tutoring import (
    DecideRequest, GenerateRequest, QuestionUnderstandRequest, QuestionUnderstandResponse,
    SubjectClassifyRequest, SubjectClassifyResponse,
)
from core.tutoring.agent_events import (
    agent_event,
    STATUS_PROCESSING,
)
from core.tutoring.decider import iter_decide_events
from core.tutoring.generator import iter_tokens
from core.tutoring.question_understand import understand_question
from core.tutoring.subject_classify import classify_subject

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tutoring", tags=["Tutoring"])


def _sse(event: str, data: dict) -> str:
    """格式化 SSE 事件行"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/decide")
async def tutoring_decide(
    request: DecideRequest,
    x_internal_token: str = Header(None),
):
    """决策端点(流式 SSE): 先发 agent 思考阶段,再 thinking*(真实推理),再 meta(ActionMeta),最后 done。

    BREAKING(相对 ai-tutoring): 响应从 JSON 改 SSE 流。Java 解析 SSE 提取 meta 事件。
    403/422 仍在流式前返回(与改造前一致)。
    Java 每轮先调 decide → 护栏审批 type(从 meta 取)→ 再调 generate。
    thinking 事件为附加内容流(豆包真实推理),Java 过滤 meta 时自动忽略,零改动。
    """
    verify_internal_token(x_internal_token)

    async def decide_stream():
        try:
            yield _sse("agent", agent_event("perceive"))
            yield _sse("agent", agent_event("analyze", status=STATUS_PROCESSING))
            yield _sse("agent", agent_event("plan", status=STATUS_PROCESSING))

            # 流式决策: thinking*(真实推理)→ agent(decide)→ meta(换题短路/降级兜底均保证合法)
            for ev in iter_decide_events(request):
                if ev["event"] == "meta":
                    yield _sse("agent", agent_event("decide"))
                yield _sse(ev["event"], ev["data"])

            yield _sse("done", {
                "model_used": f"{settings.TUTORING_DECIDE_PROVIDER}/{settings.TUTORING_DECIDE_MODEL}",
            })
        except Exception as e:
            logger.error("decide failed: %s", e)
            yield _sse("error", {"code": "500", "message": "decide failed"})

    return StreamingResponse(
        decide_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/generate")
async def tutoring_generate(
    request: GenerateRequest,
    x_internal_token: str = Header(None),
):
    """生成端点(流式 SSE): 按已放行的 action_type 流式返回正文。

    事件序列: meta(已放行 type)→ agent(generate)→ token* → agent(memory)→ done。
    (memory 为 Python 占位;Java 真实落库后可再发完成事件)
    中段失败 → event: error,流终止(Java 不可重试,提示重发)。
    """
    verify_internal_token(x_internal_token)

    async def generate_stream():
        try:
            for ev in iter_tokens(request):
                if ev["event"] == "meta":
                    # 类型先行: 先发 meta(action_type),再进入生成阶段
                    yield _sse("meta", ev["data"])
                    yield _sse("agent", agent_event("generate", status=STATUS_PROCESSING))
                else:
                    # 注: memory 事件由 Java 在真实落库后发(Python 不发占位,避免双发)
                    yield _sse(ev["event"], ev["data"])
        except Exception as e:
            logger.error("generate failed: %s", e)
            yield _sse("error", {"code": "500", "message": "生成失败"})

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/question-understand", response_model=QuestionUnderstandResponse)
async def tutoring_question_understand(
    request: QuestionUnderstandRequest,
    x_internal_token: str = Header(None),
):
    """视觉题目理解(无会话,一请求一返回 JSON)。

    看图 → 题型名 + 顺带知识点。视觉失败 → 空 topic_labels(Java 降级 PENDING,不视为错误)。
    不同于 decide/generate(SSE): 本端点同步 JSON,模型写死 doubao(design D1/D3)。
    字段 snake_case(与 decide/generate 一致);直接返回模型 JSON(同 /api/llm/chat 惯例)。
    """
    verify_internal_token(x_internal_token)
    return understand_question(request)


@router.post("/subject-classify", response_model=SubjectClassifyResponse)
async def tutoring_subject_classify(
    request: SubjectClassifyRequest,
    x_internal_token: str = Header(None),
):
    """学科分类(decide 之前,学科门): 文本/图片 → 闭集 subject。

    Java 在 decide 前调用,非 math 跳过(不建/不续会话、不落库)。失败 → 空 subject
    (Java 按 math 放行,不阻断答疑)。不同于 decide/generate(SSE): 本端点同步 JSON,
    模型写死 doubao(与 question-understand 同款,见 subject_classify.py)。
    字段 snake_case;直接返回模型 JSON(同 /api/llm/chat 惯例)。
    """
    verify_internal_token(x_internal_token)
    return classify_subject(request)
