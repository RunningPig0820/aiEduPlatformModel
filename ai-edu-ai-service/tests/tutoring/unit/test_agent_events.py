"""
任务 1: agent 事件协议测试(思考流程展示的标准事件)

标准阶段表 + AgentEvent 构造辅助 + level/status + 中文 label
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)


class TestAgentEventProtocol:
    """agent 事件协议"""

    def test_stages_complete(self):
        """标准阶段表齐全(8 个)"""
        from core.tutoring.agent_events import STAGES

        assert STAGES == {
            "perceive", "analyze", "plan", "tool",
            "decide", "generate", "memory", "guardrail",
        }

    def test_event_format(self):
        """事件格式 {level,stage,label,status,detail}"""
        from core.tutoring.agent_events import agent_event

        ev = agent_event(stage="plan")
        assert set(ev.keys()) == {"level", "stage", "label", "status", "detail"}
        assert ev["stage"] == "plan"
        assert ev["status"] == "done"    # 默认
        assert ev["level"] == "sub"      # 默认
        assert ev["detail"] is None

    def test_label_default_chinese(self):
        """label 默认用中文展示文案"""
        from core.tutoring.agent_events import agent_event, STAGE_LABELS

        ev = agent_event(stage="perceive")
        assert ev["label"] == "读取题目"
        assert STAGE_LABELS["decide"] == "决策完成"
        assert STAGE_LABELS["guardrail"] == "安全把关"

    def test_level_master_supported(self):
        """level 支持 master(主 agent 编排预留)"""
        from core.tutoring.agent_events import agent_event

        ev = agent_event(stage="plan", level="master")
        assert ev["level"] == "master"

    def test_detail_and_status_custom(self):
        """detail/status 可定制(工具结果、进行中状态等)"""
        from core.tutoring.agent_events import agent_event

        ev = agent_event(stage="tool", status="processing", detail="查询掌握度")
        assert ev["status"] == "processing"
        assert ev["detail"] == "查询掌握度"

    def test_custom_label_overrides(self):
        """显式 label 覆盖默认中文文案"""
        from core.tutoring.agent_events import agent_event

        ev = agent_event(stage="generate", label="正在组织思路")
        assert ev["label"] == "正在组织思路"
