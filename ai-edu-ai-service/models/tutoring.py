"""
AI 答疑数据模型 - Java 后端与 Python Agent 的契约层

纯数据定义,无业务逻辑。既是 FastAPI 请求/响应校验的 Pydantic 模型,
也是 structured.py 做 function calling 结构化输出时绑定给 LLM 的 schema。

对齐文档: openspec/changes/ai-tutoring/api.md + design.md(决策 3/7)
"""
from typing import List, Optional, Literal
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


# ============ 2.1 枚举(闭集词汇表) ============


class ActionType(str, Enum):
    """decide 输出动作类型 - 闭集,Java 护栏据此放行/拒绝"""
    HINT = "hint"            # 引导提示(反问,不含步骤)
    APPROACH = "approach"    # 思路大纲(步骤+关键公式,不含最终数值)
    REVEAL = "reveal"        # 完整解答(仅当 Java 已放行)
    CONCEPT = "concept"      # 澄清/追问(模糊输入不终止)
    SWITCH = "switch"        # 换题(new_question 必填)
    END = "end"              # 收尾(end_reason 联动)


class EmotionF7(str, Enum):
    """情绪 F7 七态 - Python 侧权威,Java 存储侧对齐"""
    NEUTRAL = "NEUTRAL"            # 平静/中性(默认态,无明显情绪)
    CONFUSED = "CONFUSED"          # 困惑(没看懂题意/思路卡住)
    FRUSTRATED = "FRUSTRATED"      # 沮丧(屡次受挫/失去耐心)
    ANXIOUS = "ANXIOUS"            # 焦虑(担心做错/有压力)
    CONFIDENT = "CONFIDENT"        # 自信(掌握得好/答题顺畅)
    INTERESTED = "INTERESTED"      # 感兴趣(主动追问/好奇心强)
    BORED = "BORED"                # 无聊(内容太简单/重复讲解)


class MasterySignal(str, Enum):
    """掌握度信号"""
    MASTERED = "mastered"        # 已掌握(能独立解出)
    PRACTICING = "practicing"    # 练习中(会但需引导/会出错)
    STRUGGLING = "struggling"    # 薄弱(明显困难/多次出错)


class EndReason(str, Enum):
    """收尾原因 - 与 type=end 联动"""
    COMPLETED = "COMPLETED"              # 独立解出
    ANSWER_REVEALED = "ANSWER_REVEALED"  # 答案已给出
    ABANDONED = "ABANDONED"              # 学生放弃
    ROUND_LIMIT = "ROUND_LIMIT"          # 轮次上限


# ============ 基础子结构 ============


class ChatTurn(BaseModel):
    """对话轮次(文本与图片双通道,见 design 决策 14)

    extra='ignore': 显式固化"容忍附加字段"契约。Java 会在历史消息上附加 thinking
    字段(仅 Java 存储/前端展示用),出现在 decide/generate 请求里应被静默忽略;
    防止未来误开严格模式(extra='forbid')导致校验失败。
    """
    model_config = ConfigDict(extra="ignore")

    role: Literal["user", "ai"] = Field(..., description="角色: user/ai")
    content: str = Field(default="", description="消息内容(图片消息可为空)")
    image_url: Optional[str] = Field(None, description="图片消息的 COS 签名 URL(题目图片);无图时为 None(纯文本通道)")


class KpSnapshot(BaseModel):
    """掌握度快照条目(Java 从 t_student_kp_mastery 组装)"""
    kp_key: str = Field(..., description="TextbookKP URI")
    label: str = Field(..., description="知识点名(冗余,便于展示与 label 接地)")
    mastery_level: int = Field(default=0, ge=0, le=100, description="掌握度 0-100")


# ============ 2.2 评估与掌握度信号 ============


class Eval(BaseModel):
    """学生回答评估 - 独立子结构(设计决策 7,将来可单独拆调用)"""
    correct: bool = Field(..., description="回答是否正确")
    error_type: Optional[str] = Field(None, description="错误类型(如 '设未知数错误')")
    emotion: EmotionF7 = Field(default=EmotionF7.NEUTRAL, description="F7 七态")
    exercise_complete: bool = Field(default=False, description="是否独立解出")


class MasterySignalItem(BaseModel):
    """掌握度信号 - kp_label 接地到 mastery_snapshot 候选"""
    kp_label: str = Field(..., description="知识点 label(优先复用快照候选)")
    signal: MasterySignal = Field(..., description="掌握度信号")


# ============ 2.3 decide 输出 ActionMeta ============


class Decision(BaseModel):
    """决策部分 - 独立子结构(设计决策 7,将来单独绑定函数调用)"""
    type: ActionType = Field(..., description="动作类型闭集")
    new_question: Optional[str] = Field(None, description="switch 时的新题文本")
    end_reason: Optional[EndReason] = Field(None, description="type=end 时的收尾原因")
    safety_flag: bool = Field(default=False, description="高危内容标记(拦截由 Java 执行)")


class ActionMeta(BaseModel):
    """decide 输出动作元数据 - Java 护栏审批的依据

    平铺契约(与 api.md 一致): type / new_question / end_reason / safety_flag
    在顶层, eval 是嵌套子结构。Decision 字段在 ActionMeta 中平铺展开,
    拆次调用时直接用 Decision/Eval 绑定 schema,契约不变。
    """
    type: ActionType = Field(..., description="动作类型(硬信号,Java 据此放行)")
    reason: Optional[str] = Field(None, description="决策理由(可选,调试用)")
    eval: Eval = Field(..., description="学生回答评估(软信号)")
    mastery_signals: List[MasterySignalItem] = Field(default_factory=list, description="掌握度信号")
    new_question: Optional[str] = Field(None, description="switch 时的新题文本")
    end_reason: Optional[EndReason] = Field(None, description="type=end 时的收尾原因")
    summary: Optional[str] = Field(None, description="收尾总结")
    safety_flag: bool = Field(default=False, description="高危内容标记")
    degraded: bool = Field(default=False, description="结构化输出兜底标记(四段管线全失败时 true,Java 监控降级频次)")


# ============ 2.4 请求模型 ============


class DecideRequest(BaseModel):
    """decide 请求 - Java 每轮调用,返回 ActionMeta(非流式)

    无 current_question 字段: 当前题目由 Python 从 history 推断(Java 零题目状态,
    只认 type=switch 重置计数)。题目文本作为对话历史上首条 user 消息进入历史。
    """
    history: List[ChatTurn] = Field(..., description="对话历史(Java 从 Redis 组装,题目在历史中)")
    round_count: int = Field(..., ge=0, description="轮次计数")
    answer_request_count: int = Field(default=0, ge=0, description="已请求答案次数")
    mastery_snapshot: List[KpSnapshot] = Field(default_factory=list, description="学生已有掌握度(label 候选)")
    subject_hint: str = Field(default="math", description="学科(本期恒为 math)")
    is_new_question: bool = Field(default=False, description="本轮是否新题目(Java 检测到新题图/新题时置 true;Python 短路直接返回 switch,不调 LLM)")


class GenerateRequest(BaseModel):
    """generate 请求 - Java 护栏放行后调用,返回流式正文(SSE)

    无 current_question 字段: 题目文本在 history 中,由 Python 推断(与 decide 一致)。
    """
    history: List[ChatTurn] = Field(..., description="对话历史(题目在历史中)")
    subject_hint: str = Field(default="math", description="学科")
    action_type: ActionType = Field(..., description="已放行的动作类型(Java 已审批)")
    action_meta: Optional[ActionMeta] = Field(None, description="Java 放行时附带的决策元数据")
