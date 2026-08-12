"""
任务 1.2: TUTORING_* 配置测试

验证 Settings 新增配置:
- TUTORING_DECIDE_PROVIDER / TUTORING_DECIDE_MODEL
- TUTORING_GENERATE_PROVIDER / TUTORING_GENERATE_MODEL
- TUTORING_DECIDE_TEMPERATURE / TUTORING_GENERATE_TEMPERATURE

默认值指向 deepseek-v4-flash(测试走流程,见 design 决策 6)。
"""
import pytest


@pytest.fixture
def fresh_settings(monkeypatch):
    """构造全新 Settings 实例(不用模块级单例,避免环境污染)"""
    from config.settings import Settings

    return Settings()


class TestTutoringSettings:
    """TUTORING_* 配置默认值"""

    def test_decide_default_config(self, fresh_settings):
        """decide 默认走豆包(看图答疑需视觉能力)"""
        assert fresh_settings.TUTORING_DECIDE_PROVIDER == "doubao"
        assert fresh_settings.TUTORING_DECIDE_MODEL == "doubao-seed-2-0-mini-260428"

    def test_generate_default_config(self, fresh_settings):
        """generate 默认走豆包(看图答疑需视觉能力)"""
        assert fresh_settings.TUTORING_GENERATE_PROVIDER == "doubao"
        assert fresh_settings.TUTORING_GENERATE_MODEL == "doubao-seed-2-0-mini-260428"

    def test_temperature_defaults(self, fresh_settings):
        """温度默认值: decide 偏低(判断密集), generate 偏高(内容生成)"""
        assert fresh_settings.TUTORING_DECIDE_TEMPERATURE == 0.3
        assert fresh_settings.TUTORING_GENERATE_TEMPERATURE == 0.7

    def test_env_override(self, monkeypatch):
        """环境变量可覆盖默认值"""
        from config.settings import Settings

        monkeypatch.setenv("TUTORING_DECIDE_MODEL", "glm-4-flash")
        monkeypatch.setenv("TUTORING_GENERATE_TEMPERATURE", "0.5")
        s = Settings()

        assert s.TUTORING_DECIDE_MODEL == "glm-4-flash"
        assert s.TUTORING_GENERATE_TEMPERATURE == 0.5
