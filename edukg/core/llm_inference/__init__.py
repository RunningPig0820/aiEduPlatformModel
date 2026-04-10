"""
LLM 推理核心模块

提供双模型投票机制，用于前置关系推断和知识点匹配。

主要组件:
- DualModelVoter: 双模型投票器（GLM-4-flash + DeepSeek）
- PrerequisiteInferer: 前置关系推断器
- PromptTemplates: LLM Prompt 模板
"""

from edukg.core.llm_inference.dual_model_voter import DualModelVoter
from edukg.core.llm_inference.prompt_templates import (
    PREREQUISITE_PROMPT,
    KP_MATCH_PROMPT,
)
from edukg.core.llm_inference.prerequisite_inferer import PrerequisiteInferer

__all__ = [
    "DualModelVoter",
    "PrerequisiteInferer",
    "PREREQUISITE_PROMPT",
    "KP_MATCH_PROMPT",
]