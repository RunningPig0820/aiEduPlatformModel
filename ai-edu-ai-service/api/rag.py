"""
RAG API路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    subject: Optional[str] = None
    difficulty: Optional[str] = None


class SearchResult(BaseModel):
    question_id: int
    content: str
    similarity: float
    knowledge_point: str


@router.post("/search", response_model=List[SearchResult])
async def search_similar_questions(request: SearchRequest):
    """
    搜索相似题目（举一反三）
    """
    # TODO: 实现向量检索
    return [
        SearchResult(
            question_id=1,
            content="相似题目1",
            similarity=0.95,
            knowledge_point="知识点A"
        ),
        SearchResult(
            question_id=2,
            content="相似题目2",
            similarity=0.88,
            knowledge_point="知识点A"
        )
    ]


@router.post("/embed")
async def embed_question(question: str):
    """
    生成题目向量
    """
    # TODO: 实现向量化
    return {
        "question": question,
        "vector_dimension": 768
    }