"""
视觉题目理解 - 看图识别题型(题型分析图片入口,方案 B)

独立 stateless 端点复用 decide 的看图能力:
- 模型写死 doubao(全模态, allowed+vision, 与看图答疑同款),不做路由/白名单(design D1/D3)
- HumanMessage([{text}, {image_url}]) → ChatOpenAI(ark),与 decide 看图同一路径
- 输出: 1~5 个题型名(去编号/bullet 拆行)+ 顺带知识点
- 绝不抛异常: LLM 失败/解析失败 → 空 topic_labels(Java 降级 PENDING)

对齐: openspec/changes/ai-tutoring-question-understand/design.md D2~D5
"""
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from core.gateway.factory import LLMFactory
from models.tutoring import QuestionUnderstandRequest, QuestionUnderstandResponse

logger = logging.getLogger(__name__)

# 视觉题目理解模型 - 写死 doubao(全模态, allowed+vision),与看图答疑同款(design D3)。
# 不做路由/白名单: 非视觉模型在构造上不可能进入本端点。
_UNDERSTAND_PROVIDER = "doubao"
_UNDERSTAND_MODEL = "doubao-seed-2-0-mini-260428"
_UNDERSTAND_TEMPERATURE = 0.3

# 题型名上限(与 Java KpQuestionAnalyzer 的 1~5 一致)
_MAX_TOPIC_LABELS = 5

_SYSTEM_TEMPLATE = """你是数学题型的"识别器"。看这张题目图片，完成两个任务：

1. 识别题型：输出 1~{max} 个题型名，每行一个。不要编号、不要解释、不要多余文字。
2. 顺带知识点（可选）：如果还看得出这道题涉及的学科知识点，在最后另起一行，以"知识点："开头，用逗号分隔列出；看不出就跳过。

{word_bank}
图片无法辨认或不是数学题时，只输出"无法识别"。
"""

_WORD_BANK_HINT = """## 参考题型名（优先从这些名字里选，词汇不足可自拟）
{labels}
"""

# 去编号/bullet 前缀: "1." "1、" "1)" "-" "•" ">" 等(LLM 偶发带编号,宽容处理)
_BULLET_PREFIX = re.compile(r"^\s*(?:\d+[\.、)）]|[-•*>]\s*)\s*")


def _build_system(topic_hint) -> str:
    word_bank = _WORD_BANK_HINT.format(labels="、".join(topic_hint)) if topic_hint else ""
    return _SYSTEM_TEMPLATE.format(max=_MAX_TOPIC_LABELS, word_bank=word_bank)


def _parse_labels(text: str):
    """解析模型输出 → (topic_labels, question_kps)。去编号/bullet 拆行。"""
    topic_labels, question_kps = [], []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("知识点：") or line.startswith("知识点:"):
            for kp in re.split(r"[、,，]", line.split("：", 1)[-1].split(":", 1)[-1]):
                kp = kp.strip()
                if kp:
                    question_kps.append(kp)
            continue
        if "无法识别" in line or "无法辨认" in line:
            continue
        cleaned = _BULLET_PREFIX.sub("", line).strip(" \t\"'“”`")
        if cleaned:
            topic_labels.append(cleaned)
    return topic_labels[:_MAX_TOPIC_LABELS], question_kps


def understand_question(request: QuestionUnderstandRequest, llm=None) -> QuestionUnderstandResponse:
    """看图 → 题型名 + 顺带知识点。绝不抛异常,失败返回空 topic_labels。

    Args:
        request: 视觉题目理解请求(image_url 必填)
        llm: 注入用(测试);默认写死 doubao 视觉模型
    """
    try:
        llm = llm or LLMFactory.create(
            _UNDERSTAND_PROVIDER, _UNDERSTAND_MODEL, temperature=_UNDERSTAND_TEMPERATURE,
            # 关思考(与 decide 同款): doubao mini 默认开思考 = 先写草稿再答,
            # 实测开思考 50~145s、关思考看图 1.2s(见 ark_stream.py 注释)——32s+ 卡顿根源。
            extra_body={"thinking": {"type": "disabled"}},
            # 无内部超时 → openai SDK 默认 600s 才失败;设 20s + 关 SDK 重试,
            # 慢/失败快速返回空 topic_labels(Java 降级 PENDING),不让调用方无限等。
            request_timeout=20,
            max_retries=0,
        )
        messages = [
            SystemMessage(content=_build_system(request.topic_hint)),
            HumanMessage(content=[
                {"type": "text", "text": "请识别这张题目图片的题型。"},
                {"type": "image_url", "image_url": {"url": request.image_url}},
            ]),
        ]
        content = llm.invoke(messages).content or ""
        topic_labels, question_kps = _parse_labels(content)
        logger.info(
            "question_understand: 识别 %d 个题型, %d 个知识点",
            len(topic_labels), len(question_kps),
        )
        return QuestionUnderstandResponse(
            topic_labels=topic_labels,
            question_kps=question_kps or None,
        )
    except Exception as e:
        logger.warning("question_understand 失败,降级空结果: %s", e)
        return QuestionUnderstandResponse()
