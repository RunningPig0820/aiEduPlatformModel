"""
工具调用支持
"""
from langchain_core.tools import tool
from typing import List, Dict, Any, Optional


# ============ 示例工具定义 ============
# 这些工具可以绑定到 LLM，让 LLM 可以调用

@tool
def search_questions(keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    搜索题库中的题目

    Args:
        keyword: 搜索关键词
        limit: 返回数量限制，默认5条

    Returns:
        题目列表
    """
    # TODO: 实际实现需要调用 Java MCP Server
    return [
        {"id": 1, "title": f"关于{keyword}的题目1", "difficulty": "medium"},
        {"id": 2, "title": f"关于{keyword}的题目2", "difficulty": "hard"},
    ]


@tool
def get_student_progress(student_id: int) -> Dict[str, Any]:
    """
    获取学生的学习进度

    Args:
        student_id: 学生ID

    Returns:
        学习进度信息
    """
    # TODO: 实际实现需要调用 Java MCP Server
    return {
        "student_id": student_id,
        "completed_courses": 5,
        "total_courses": 10,
        "average_score": 85.5
    }


@tool
def submit_homework(homework_id: int, content: str) -> Dict[str, Any]:
    """
    提交作业

    Args:
        homework_id: 作业ID
        content: 作业内容

    Returns:
        提交结果
    """
    # TODO: 实际实现需要调用 Java MCP Server
    return {
        "success": True,
        "homework_id": homework_id,
        "message": "作业已提交"
    }


# ============ 工具注册表 ============

AVAILABLE_TOOLS = {
    "search_questions": search_questions,
    "get_student_progress": get_student_progress,
    "submit_homework": submit_homework,
}


def get_tool(tool_name: str):
    """获取工具"""
    return AVAILABLE_TOOLS.get(tool_name)


def get_all_tools() -> list:
    """获取所有工具"""
    return list(AVAILABLE_TOOLS.values())


def get_tools_by_names(tool_names: List[str]) -> list:
    """根据名称列表获取工具"""
    return [AVAILABLE_TOOLS[name] for name in tool_names if name in AVAILABLE_TOOLS]