"""
LLM Prompt 模板集合

提供前置关系推断和知识点匹配的 Prompt 模板。
支持从文件加载，后续可扩展从数据库加载。
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ============ 提示词文件路径 ============
PROMPTS_DIR = Path(__file__).parent / "prompts"


class PromptLoader:
    """
    提示词加载器

    支持多种加载方式：
    1. 从文件加载（默认）
    2. 从数据库加载（后续扩展）
    3. 从缓存加载

    Example:
        >>> loader = PromptLoader()
        >>> prompt = loader.load("prerequisite")
        >>> formatted = loader.format(prompt, kp_a_name="加法", ...)
    """

    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        初始化提示词加载器

        Args:
            prompts_dir: 提示词文件目录（默认使用内置目录）
        """
        self.prompts_dir = prompts_dir or PROMPTS_DIR
        self._cache: dict = {}

    def load(self, name: str, use_cache: bool = True) -> str:
        """
        加载提示词模板

        Args:
            name: 提示词名称（如 "prerequisite", "kp_match"）
            use_cache: 是否使用缓存

        Returns:
            提示词模板字符串
        """
        # 检查缓存
        if use_cache and name in self._cache:
            return self._cache[name]

        # 从文件加载
        prompt = self._load_from_file(name)

        # 缓存
        if use_cache and prompt:
            self._cache[name] = prompt

        return prompt

    def _load_from_file(self, name: str) -> str:
        """
        从文件加载提示词

        Args:
            name: 提示词名称

        Returns:
            提示词模板字符串
        """
        filepath = self.prompts_dir / f"{name}.txt"

        if not filepath.exists():
            raise FileNotFoundError(f"提示词文件不存在: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_from_db(self, name: str) -> str:
        """
        从数据库加载提示词（预留扩展）

        Args:
            name: 提示词名称

        Returns:
            提示词模板字符串
        """
        # TODO: 后续实现从 MySQL 加载
        raise NotImplementedError("数据库加载尚未实现")

    def format(self, template: str, **kwargs) -> str:
        """
        格式化提示词

        Args:
            template: 提示词模板
            **kwargs: 模板变量

        Returns:
            格式化后的提示词
        """
        return template.format(**kwargs)

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


# ============ 全局加载器实例 ============
_loader = PromptLoader()


# ============ 便捷函数 ============
def get_prerequisite_prompt() -> str:
    """获取前置关系推断提示词"""
    return _loader.load("prerequisite")


def get_kp_match_prompt() -> str:
    """获取知识点匹配提示词"""
    return _loader.load("kp_match")


def get_definition_deps_prompt() -> str:
    """获取定义依赖抽取提示词"""
    return _loader.load("definition_deps")


def get_textbook_kg_prompt() -> str:
    """获取教学知识点推断提示词"""
    return _loader.load("textbook_kg")


def format_prerequisite_prompt(
    kp_a_name: str,
    kp_a_description: str,
    kp_b_name: str,
    kp_b_description: str
) -> str:
    """
    格式化前置关系推断 Prompt

    Args:
        kp_a_name: 知识点A名称
        kp_a_description: 知识点A描述
        kp_b_name: 知识点B名称
        kp_b_description: 知识点B描述

    Returns:
        格式化后的 Prompt
    """
    template = get_prerequisite_prompt()
    return _loader.format(
        template,
        kp_a_name=kp_a_name,
        kp_a_description=kp_a_description or "无描述",
        kp_b_name=kp_b_name,
        kp_b_description=kp_b_description or "无描述"
    )


def format_kp_match_prompt(
    textbook_kp_name: str,
    textbook_kp_description: str,
    kg_kp_name: str,
    kg_kp_description: str
) -> str:
    """
    格式化知识点匹配 Prompt

    Args:
        textbook_kp_name: 教材知识点名称
        textbook_kp_description: 教材知识点描述
        kg_kp_name: 知识图谱知识点名称
        kg_kp_description: 知识图谱知识点描述

    Returns:
        格式化后的 Prompt
    """
    template = get_kp_match_prompt()
    return _loader.format(
        template,
        textbook_kp_name=textbook_kp_name,
        textbook_kp_description=textbook_kp_description or "无描述",
        kg_kp_name=kg_kp_name,
        kg_kp_description=kg_kp_description or "无描述"
    )


def format_definition_deps_prompt(
    kp_name: str,
    kp_definition: str,
    kp_list: str
) -> str:
    """
    格式化定义依赖抽取 Prompt

    Args:
        kp_name: 知识点名称
        kp_definition: 知识点定义
        kp_list: 已知知识点列表（字符串形式）

    Returns:
        格式化后的 Prompt
    """
    template = get_definition_deps_prompt()
    return _loader.format(
        template,
        kp_name=kp_name,
        kp_definition=kp_definition or "无定义",
        kp_list=kp_list
    )


def format_textbook_kg_prompt(
    stage: str,
    grade: str,
    semester: str,
    chapter_name: str,
    section_name: str,
    existing_kps: list
) -> str:
    """
    格式化教学知识点推断 Prompt

    Args:
        stage: 学段（小学/初中/高中）
        grade: 年级（一年级/七年级/必修第一册）
        semester: 册次（上册/下册）
        chapter_name: 章节名称
        section_name: 小节名称
        existing_kps: 已有知识点列表

    Returns:
        格式化后的 Prompt
    """
    template = get_textbook_kg_prompt()
    existing_kps_str = str(existing_kps) if existing_kps else "[]"
    return _loader.format(
        template,
        stage=stage,
        grade=grade,
        semester=semester,
        chapter_name=chapter_name,
        section_name=section_name,
        existing_kps=existing_kps_str
    )


# ============ 向后兼容：保留原有的常量（从文件加载） ============
PREREQUISITE_PROMPT = get_prerequisite_prompt()
KP_MATCH_PROMPT = get_kp_match_prompt()
DEFINITION_DEPS_PROMPT = get_definition_deps_prompt()
TEXTBOOK_KG_PROMPT = get_textbook_kg_prompt()