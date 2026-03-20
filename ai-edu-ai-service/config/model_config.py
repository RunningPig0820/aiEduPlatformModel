"""
模型配置
"""
from typing import Dict, Tuple, Any

# ============ 支持的模型配置 ============

MODEL_CONFIG: Dict[str, Dict[str, Any]] = {
    "zhipu": {
        "display_name": "智谱 AI",
        "models": {
            "glm-4-flash": {
                "display_name": "GLM-4-Flash",
                "free": True,
                "supports_tools": True,
                "supports_vision": False,
                "description": "免费模型，适合大多数场景"
            },
            "glm-4.5-air": {
                "display_name": "GLM-4.5-Air",
                "free": False,
                "supports_tools": True,
                "supports_vision": False,
                "description": "均衡模型"
            },
            "glm-4.6v": {
                "display_name": "GLM-4.6V",
                "free": False,
                "supports_tools": True,
                "supports_vision": True,
                "description": "视觉模型，支持图片理解"
            },
            "glm-4.7": {
                "display_name": "GLM-4.7",
                "free": False,
                "supports_tools": True,
                "supports_vision": False,
                "description": "最强模型"
            }
        },
        "default_model": "glm-4-flash"
    },
    "deepseek": {
        "display_name": "DeepSeek",
        "models": {
            "deepseek-chat": {
                "display_name": "DeepSeek Chat",
                "free": False,
                "supports_tools": True,
                "supports_vision": False,
                "description": "通用对话模型"
            },
            "deepseek-coder": {
                "display_name": "DeepSeek Coder",
                "free": False,
                "supports_tools": True,
                "supports_vision": False,
                "description": "代码专用模型"
            }
        },
        "default_model": "deepseek-chat"
    },
    "bailian": {
        "display_name": "阿里百炼",
        "models": {
            "qwen-turbo": {
                "display_name": "Qwen-Turbo",
                "free": False,
                "supports_tools": True,
                "supports_vision": False,
                "description": "快速响应模型"
            },
            "qwen-plus": {
                "display_name": "Qwen-Plus",
                "free": False,
                "supports_tools": True,
                "supports_vision": False,
                "description": "增强模型"
            }
        },
        "default_model": "qwen-turbo"
    }
}


# ============ 场景到模型的映射 ============

SCENE_MODEL_MAPPING: Dict[str, Tuple[str, str]] = {
    # 免费！页面解释用免费模型足够
    "page_assistant": ("zhipu", "glm-4-flash"),

    # 作业批改需要深度理解
    "homework_grading": ("deepseek", "deepseek-chat"),

    # FAQ 用免费模型足够
    "faq": ("zhipu", "glm-4-flash"),

    # 图片理解需要视觉模型
    "image_analysis": ("zhipu", "glm-4.6v"),

    # 内容生成
    "content_generation": ("deepseek", "deepseek-chat"),
}

# 默认场景配置
DEFAULT_SCENE = ("zhipu", "glm-4-flash")


def get_model_for_scene(scene: str) -> Tuple[str, str]:
    """
    根据场景获取推荐模型

    Args:
        scene: 场景代码

    Returns:
        Tuple[str, str]: (provider, model)
    """
    return SCENE_MODEL_MAPPING.get(scene, DEFAULT_SCENE)


def get_free_models() -> list:
    """获取所有免费模型"""
    free_models = []
    for provider, config in MODEL_CONFIG.items():
        for model, model_config in config["models"].items():
            if model_config.get("free", False):
                free_models.append({
                    "provider": provider,
                    "model": model,
                    "display_name": model_config["display_name"]
                })
    return free_models


def get_all_providers() -> list:
    """获取所有 provider 信息"""
    result = []
    for provider, config in MODEL_CONFIG.items():
        result.append({
            "name": provider,
            "display_name": config["display_name"],
            "models": [
                {
                    "name": model,
                    **model_config
                }
                for model, model_config in config["models"].items()
            ]
        })
    return result