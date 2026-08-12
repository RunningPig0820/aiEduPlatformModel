"""
agent 事件协议 - 思考流程展示的标准事件

标准事件格式: {level, stage, label, status, detail}
- level: sub(子 agent)/ master(主 agent 编排,预留)
- stage: 标准阶段(perceive/analyze/plan/tool/decide/generate/memory/guardrail)
- label: 前端展示文案(默认中文)
- status: processing/done/error
- detail: 可选补充(工具结果/决策摘要)

对齐: openspec/changes/tutoring-agent-protocol/(design 决策 2 / api.md)
"""
from typing import Dict, Optional, Set, TypedDict

# ============ 标准阶段表 ============

STAGES: Set[str] = {
    "perceive",    # 感知输入
    "analyze",     # 意图/需求解析
    "plan",        # 规划任务
    "tool",        # 工具调用(预留,将来知识图谱 agent)
    "decide",      # 决策完成
    "generate",    # 生成中
    "memory",      # 记忆更新
    "guardrail",   # 安全把关(Java)
}

# 中文展示文案(与 api.md 对齐)
STAGE_LABELS: Dict[str, str] = {
    "perceive": "读取题目",
    "analyze": "解析意图",
    "plan": "规划引导",
    "tool": "工具调用",
    "decide": "决策完成",
    "generate": "生成中",
    "memory": "记忆更新",
    "guardrail": "安全把关",
}

# ============ level / status ============

LEVEL_SUB = "sub"
LEVEL_MASTER = "master"

STATUS_PROCESSING = "processing"
STATUS_DONE = "done"
STATUS_ERROR = "error"


# ============ 事件构造 ============

class AgentEvent(TypedDict):
    """agent 事件标准格式"""
    level: str
    stage: str
    label: str
    status: str
    detail: Optional[str]


def agent_event(
    stage: str,
    status: str = STATUS_DONE,
    label: Optional[str] = None,
    level: str = LEVEL_SUB,
    detail: Optional[str] = None,
) -> AgentEvent:
    """构造 agent 事件。

    Args:
        stage: 标准阶段(stage 属 STAGES)
        status: processing/done/error
        label: 展示文案,默认取 STAGE_LABELS
        level: sub(子 agent)/ master(主 agent 预留)
        detail: 可选补充(工具结果/决策摘要)
    """
    return {
        "level": level,
        "stage": stage,
        "label": label or STAGE_LABELS.get(stage, stage),
        "status": status,
        "detail": detail,
    }
