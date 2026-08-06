"""
任务 1.1: deepseek-v4-flash 模型注册测试

验证 deepseek-v4-flash 已注册到 MODEL_CONFIG 且:
- allowed=True(允许外部调用)
- free=False(收费模型)
"""
import sys
import os

# 项目根目录加入 sys.path(依赖 tests/conftest.py 已插入,这里冗余保险)
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)


class TestDeepSeekV4FlashRegistration:
    """deepseek-v4-flash 注册到 deepseek provider"""

    def test_model_registered_in_config(self):
        """deepseek-v4-flash 存在于 deepseek 模型表"""
        from config.model_config import MODEL_CONFIG

        assert "deepseek-v4-flash" in MODEL_CONFIG["deepseek"]["models"]

    def test_is_allowed(self):
        """允许外部调用"""
        from config.model_config import is_model_allowed

        assert is_model_allowed("deepseek", "deepseek-v4-flash") is True

    def test_is_paid(self):
        """非免费模型"""
        from config.model_config import MODEL_CONFIG

        assert MODEL_CONFIG["deepseek"]["models"]["deepseek-v4-flash"]["free"] is False

    def test_in_get_allowed_models(self):
        """出现在允许调用的模型列表"""
        from config.model_config import get_allowed_models

        assert any(
            m["full_name"] == "deepseek/deepseek-v4-flash"
            for m in get_allowed_models()
        )

    def test_not_in_get_free_models(self):
        """不应出现在免费模型列表"""
        from config.model_config import get_free_models

        assert not any(
            m["provider"] == "deepseek" and m["model"] == "deepseek-v4-flash"
            for m in get_free_models()
        )
