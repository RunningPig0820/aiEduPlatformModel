"""
RAG 项目介绍助手数据模型 - 白盒链路 ask 请求(B 组)

对齐: openspec/changes/rag-project-intro-assistant/api.md(RagAskRequest)
      snake_case 请求字段(Java 桥 snake→camel 映射后转达, 对齐 tutoring 契约纪律)
纯数据定义, 无业务逻辑; 独立于 models/rag.py(旧 1.6C 查询)。
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RagAssistantAskRequest(BaseModel):
    """白盒助手 ask 请求 - 前端/Java 网关调 `POST /api/rag/assistant/ask`。

    Python 无状态(D-D 定死): history/trace_id 由 Java 传入只消费, Python 不落会话;
    turns/close/累计 token 归 Java Redis(Python 不建 close/turns 端点)。
    """
    current_project: str = Field(default="ai-tutoring",
                                 description="页面锚定模块(ai-tutoring/rag-system 等); 缺省=当前项目")
    question: str = Field(..., min_length=1, max_length=500, description="学生问题")
    session_id: Optional[str] = Field(default=None, description="会话 id(Java 续接锚点/轮次, Python 只读)")
    history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="最近 N 轮(默认 3, 含 clarify 轮; Java 网关组装传入, 供 intent/rewrite/clarify 兜底, Python 只读)")
    trace_id: str = Field(default="", description="Java 生成传 Python; Python 贯穿日志并在 done 回显(两端 trace 一致)")
    stream: bool = Field(default=False, description="true 走 SSE 流式; false/缺省 走非流式(done + stages 摘要)")
    top_k: int = Field(default=3, ge=1, le=5, description="RRF 精排块数(建议保持默认 3)")
