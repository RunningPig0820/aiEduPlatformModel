"""
学科分类 - 学科门前置判定(decide 之前,学科无关小分类器)

独立 stateless 端点,复用 question_understand 的模式:
- 模型写死 doubao(与 decide/understand 统一 doubao-seed-2-0-mini-260428 / temp 0.3)
- HumanMessage 纯文本 或 多模态(text + image_url),复用 decide 看图路径
- 学科无关提示词: 只判学科不做解题; 拿不准 → math(宁可不误拦); 图片无法辨认/非学科 → other
- 输出: 闭集 math/physics/chemistry/biology/other; 失败/超时/闭集外 → None(Java 按 math 放行)
- 绝不抛异常; 复用 question_understand 慢修复(关思考 + 20s 超时 + 关 SDK 重试)

对齐: openspec/changes/tutoring-subject-gate/design.md 决策 2/4 + Python 侧 design.md
"""
import logging
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from core.gateway.factory import LLMFactory
from models.tutoring import SubjectClassifyRequest, SubjectClassifyResponse, SubjectType

logger = logging.getLogger(__name__)

# 学科分类模型 - 写死 doubao(与 decide/question_understand 统一,design 决策 4)
_CLASSIFY_PROVIDER = "doubao"
_CLASSIFY_MODEL = "doubao-seed-2-0-mini-260428"
_CLASSIFY_TEMPERATURE = 0.3

_VALID_SUBJECTS = {s.value for s in SubjectType}

_SYSTEM_TEMPLATE = """你是"学科识别器"。只判断一道题属于哪个学科，不解答题目。

只能输出一个学科：math / physics / chemistry / biology / chinese / english / politics / geography / history / other。

判定规则（宁可不误拦）：
- 明确数学题（代数/几何/方程/应用题/计数等）→ math
- 明确物理题 → physics；化学题 → chemistry；生物题 → biology
- 明确语文题 → chinese；英语题 → english；政治题 → politics；地理题 → geography；历史题 → history
- 图片无法辨认、内容不是学科题、或不属于以上任一学科 → other
- 拿不准该不该算数学、在 math 与其他学科之间犹豫 → 输出 math（宁可放过，不可把数学题误判成别的学科）

只输出学科名，不要解释、不要多余文字。
"""


def _parse_subject(text: str) -> Optional[str]:
    """解析模型输出 → 闭集学科或 None。

    宽容前后空白/引号/大小写/多余文字("答案:math" 等);闭集外/无法解析 → None
    (Java 按 math 放行,宁可漏拦不误拦)。
    """
    cleaned = (text or "").strip().lower()
    for s in _VALID_SUBJECTS:
        if s in cleaned:
            return s
    return None


def classify_subject(request: SubjectClassifyRequest, llm=None) -> SubjectClassifyResponse:
    """判学科 → 闭集之一;绝不抛异常,失败返回 subject=None(Java 按 math 放行)。

    Args:
        request: 学科分类请求(content/image_url 至少一个非空)
        llm: 注入用(测试);默认写死 doubao 学科分类模型
    """
    try:
        llm = llm or LLMFactory.create(
            _CLASSIFY_PROVIDER, _CLASSIFY_MODEL, temperature=_CLASSIFY_TEMPERATURE,
            # 关思考(与 question_understand 同款): doubao mini 默认开思考 = 先写草稿再答,
            # 实测开思考 50~145s、关思考秒出——学科门不能成为新卡点
            extra_body={"thinking": {"type": "disabled"}},
            request_timeout=20,
            max_retries=0,
        )
        text_content = "请判断下面这道题属于哪个学科（输出 math/physics/chemistry/biology/other 之一）："
        if request.image_url:
            human = HumanMessage(content=[
                {"type": "text", "text": text_content},
                {"type": "image_url", "image_url": {"url": request.image_url}},
            ])
        else:
            human = HumanMessage(content=f"{text_content}\n\n{request.content}")
        subject = _parse_subject(llm.invoke([SystemMessage(content=_SYSTEM_TEMPLATE), human]).content or "")
        logger.info("subject_classify: subject=%s", subject)
        return SubjectClassifyResponse(subject=subject)
    except Exception as e:
        logger.warning("subject_classify 失败,降级空 subject(Java 按 math 放行): %s", e)
        return SubjectClassifyResponse()
