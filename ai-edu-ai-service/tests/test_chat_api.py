"""
对话 API 测试
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestChatAPI:
    """对话 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def headers(self):
        """创建认证头"""
        import os
        return {"x-internal-token": os.environ.get("INTERNAL_TOKEN", "test_internal_token")}

    def test_chat_missing_token(self, client):
        """测试缺少 Token"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "scene": "page_assistant",
                "user_id": 123
            }
        )
        assert response.status_code == 403

    def test_chat_invalid_token(self, client):
        """测试无效 Token"""
        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "scene": "page_assistant",
                "user_id": 123
            },
            headers={"x-internal-token": "wrong_token"}
        )
        assert response.status_code == 403

    @patch("api.chat.ModelRouter.create_llm")
    def test_chat_success(self, mock_create_llm, client, headers):
        """测试成功对话"""
        # Mock LLM
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "这是一个测试响应"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = (mock_llm, "zhipu/glm-4-flash")

        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "scene": "page_assistant",
                "user_id": 123
            },
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["model_used"] == "zhipu/glm-4-flash"

    @patch("api.chat.ModelRouter.create_llm")
    def test_chat_with_custom_model(self, mock_create_llm, client, headers):
        """测试指定模型"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "测试响应"
        mock_response.tool_calls = []
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = (mock_llm, "deepseek/deepseek-chat")

        response = client.post(
            "/api/llm/chat",
            json={
                "message": "你好",
                "scene": "page_assistant",
                "user_id": 123,
                "model_provider": "deepseek",
                "model_name": "deepseek-chat"
            },
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["model_used"] == "deepseek/deepseek-chat"

    @patch("api.chat.ModelRouter.create_llm")
    def test_chat_with_tool_calls(self, mock_create_llm, client, headers):
        """测试工具调用响应"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = None
        mock_response.tool_calls = [
            {
                "id": "call_123",
                "name": "search_questions",
                "args": {"keyword": "数学"}
            }
        ]
        mock_llm.invoke.return_value = mock_response
        mock_create_llm.return_value = (mock_llm, "zhipu/glm-4-flash")

        response = client.post(
            "/api/llm/chat",
            json={
                "message": "帮我搜索数学题",
                "scene": "page_assistant",
                "user_id": 123
            },
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["name"] == "search_questions"

    def test_list_models(self, client, headers):
        """测试获取模型列表"""
        response = client.get("/api/llm/models", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "providers" in data["data"]
        assert "scene_defaults" in data["data"]


class TestStreamAPI:
    """流式 API 测试"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from main import app
        return TestClient(app)

    @pytest.fixture
    def headers(self):
        """创建认证头"""
        import os
        return {"x-internal-token": os.environ.get("INTERNAL_TOKEN", "test_internal_token")}

    def test_stream_missing_token(self, client):
        """测试流式 API 缺少 Token"""
        response = client.post(
            "/api/llm/chat/stream",
            json={
                "message": "你好",
                "scene": "page_assistant",
                "user_id": 123
            }
        )
        assert response.status_code == 403

    @patch("api.chat.ModelRouter.create_llm")
    def test_stream_success(self, mock_create_llm, client, headers):
        """测试流式响应成功"""
        mock_llm = MagicMock()

        # 模拟流式响应
        chunks = [
            MagicMock(content="这"),
            MagicMock(content="是"),
            MagicMock(content="测试"),
        ]
        mock_llm.stream.return_value = iter(chunks)
        mock_create_llm.return_value = (mock_llm, "zhipu/glm-4-flash")

        response = client.post(
            "/api/llm/chat/stream",
            json={
                "message": "你好",
                "scene": "page_assistant",
                "user_id": 123
            },
            headers=headers
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]