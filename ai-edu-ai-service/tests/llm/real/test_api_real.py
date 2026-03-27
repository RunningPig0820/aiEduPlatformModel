"""
API 端点真实测试
测试 FastAPI 端点安全验证
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()


def get_internal_token():
    """获取配置的 INTERNAL_TOKEN"""
    return os.getenv("INTERNAL_TOKEN", "test-token")


class TestChatAPIReal:
    """API 端点真实测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from main import app
        return TestClient(app)

    @pytest.mark.requires_zhipu
    def test_chat_default_model(self, client):
        """测试聊天 - 使用默认模型"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "user_id": 1
            },
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["model_used"] == "zhipu/glm-4-flash"  # 默认免费模型
        print(f"\n✅ 默认模型: {data['model_used']}")

    @pytest.mark.requires_zhipu
    def test_chat_allowed_model(self, client):
        """测试聊天 - 使用允许的模型"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "user_id": 1,
                "provider": "zhipu",
                "model": "glm-4-flash"
            },
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model_used"] == "zhipu/glm-4-flash"
        print(f"\n✅ 允许模型: {data['model_used']}")

    def test_chat_disallowed_model(self, client):
        """测试聊天 - 使用不允许的模型被拒绝"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "user_id": 1,
                "provider": "zhipu",
                "model": "glm-4.7"  # 配置中 allowed: false
            },
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]
        print(f"\n✅ 不允许的模型被正确拒绝")

    def test_chat_disallowed_model_bailian(self, client):
        """测试聊天 - 百炼不允许的模型"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "user_id": 1,
                "provider": "zhipu",
                "model": "glm-4.5-air"  # 配置中 allowed: false
            },
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 400
        print(f"\n✅ 智谱不允许的模型被正确拒绝")

    def test_chat_unknown_provider(self, client):
        """测试聊天 - 未知的 provider"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "user_id": 1,
                "provider": "unknown_provider"
            },
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 400
        print(f"\n✅ 未知 provider 被正确拒绝")

    @pytest.mark.requires_deepseek
    def test_chat_deepseek_model(self, client):
        """测试聊天 - DeepSeek 模型"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "user_id": 1,
                "provider": "deepseek",
                "model": "deepseek-chat"
            },
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 200
        data = response.json()
        assert "deepseek" in data["model_used"]
        print(f"\n✅ DeepSeek: {data['model_used']}")

    @pytest.mark.requires_bailian
    def test_chat_bailian_math_model(self, client):
        """测试聊天 - 百炼数学模型"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "计算: 123 + 456",
                "user_id": 1,
                "provider": "bailian",
                "model": "qwen-math-turbo"
            },
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 200
        data = response.json()
        assert "qwen-math-turbo" in data["model_used"]
        print(f"\n✅ 百炼数学: {data['model_used']}")

    def test_allowed_models_endpoint(self, client):
        """测试获取允许模型列表"""
        response = client.get(
            "/api/llm/allowed-models",
            headers={"x-internal-token": get_internal_token()}
        )

        assert response.status_code == 200
        data = response.json()
        models = data["data"]["allowed_models"]
        model_names = [m["full_name"] for m in models]

        # 验证白名单模型都在
        assert "zhipu/glm-4-flash" in model_names
        assert "deepseek/deepseek-chat" in model_names
        assert "bailian/qwen-math-turbo" in model_names

        print(f"\n✅ 允许模型: {model_names}")

    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestChatAPIStream:
    """流式 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from main import app
        return TestClient(app)

    @pytest.mark.requires_zhipu
    def test_stream_default_model(self, client):
        """测试流式聊天 - 默认模型"""
        with client.stream(
            "POST",
            "/api/llm/chat/stream",
            json={
                "message": "数到3",
                "user_id": 1
            },
            headers={"x-internal-token": get_internal_token()}
        ) as response:
            assert response.status_code == 200
            content = b""
            for chunk in response.iter_bytes():
                content += chunk
            assert len(content) > 0
            print(f"\n✅ Stream API: 收到 {len(content)} 字节")

    def test_stream_disallowed_model(self, client):
        """测试流式聊天 - 不允许的模型被拒绝"""
        response = client.post(
            "/api/llm/chat/stream",
            json={
                "message": "你好",
                "user_id": 1,
                "provider": "zhipu",
                "model": "invalid-model"
            },
            headers={"x-internal-token": get_internal_token()}
        )

        # 流式接口的错误会在开始时就返回
        assert response.status_code == 400
        print(f"\n✅ Stream 不允许的模型被拒绝")