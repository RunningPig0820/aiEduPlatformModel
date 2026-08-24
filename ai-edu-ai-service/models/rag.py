"""
RAG 查询数据模型 - 1.6C 查询 API 契约(后端/前端页面并行开工的依据)

对齐: docs/rag/ai-tutoring/每模块流水线-tasks.md 1.6C
纯数据定义, 无业务逻辑; 独立于 models/tutoring.py / models/vector.py。
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    """RAG 问答请求 - 前端/后端调 `POST /api/tutoring/rag/query`"""
    question: str = Field(..., description="面试官问题(或任意项目相关提问)")
    top_k: int = Field(default=6, ge=1, le=20, description="生成用召回块数")


class RAGReference(BaseModel):
    """引用块 - 前端渲染"来源"区块 + 点开源文件展示内容"""
    file: str = Field(..., description="文件名(引用展示)")
    file_path: str = Field(default="", description="相对语料根 docs/rag/ai-tutoring/, 前端定位源文件")
    anchor: str = Field(..., description="页面锚点")
    authority: float = Field(..., description="权威度(1.0 完善文档 / 0.7-0.8 原始语料)")
    summary: str = Field(default="", description="一句话'解决什么问题'")


class RAGIntent(BaseModel):
    """意图钩子输出(1.6B) - 前端可展示'命中了哪些页'"""
    locked_sections: List[str] = Field(default_factory=list, description="锚定锁定的完善文档节(01~08)")
    strategy: str = Field(default="retrieve", description="检索策略(未来意图驱动选择)")


class RAGQueryResponse(BaseModel):
    """RAG 问答响应 - 稳定返回结构, 降级后也保持一致"""
    answer: str = Field(..., description="面试口述风格答案; 降级时可能为提示语/拒答语")
    references: List[RAGReference] = Field(default_factory=list, description="命中引用块(前端来源区块)")
    intent: RAGIntent = Field(default_factory=RAGIntent, description="意图钩子输出")
    version: str = Field(default="", description="命中语料版本(YYYY-MM-DD-<sha1[:6]>, 数据时效标注)")
