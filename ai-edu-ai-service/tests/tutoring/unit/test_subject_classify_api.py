"""
任务 3.2: subject-classify API 端点测试(对齐 test.md API-001~005)

覆盖:
- 缺 token → 403 / 非法 token → 403 / 合法 token → 正常
- 全空参数(content+image_url 均空)→ 422
- 正常请求 → 200 + subject(mock classify_subject,不打真实 LLM)
- 分类失败 → 200 + subject=null(Java 按 math 放行,不 5xx)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.tutoring import router as tutoring_router
from config.settings import settings

app = FastAPI()
app.include_router(tutoring_router)
client = TestClient(app)

AUTH = {"x-internal-token": settings.INTERNAL_TOKEN}


@pytest.fixture
def mock_classify(monkeypatch):
    """mock api.tutoring.classify_subject,按需返回固定 subject。"""
    def _set(subject=None):
        from models.tutoring import SubjectClassifyResponse
        monkeypatch.setattr(
            "api.tutoring.classify_subject",
            lambda req: SubjectClassifyResponse(subject=subject),
        )
    return _set


class TestSubjectClassifyAPI:
    def test_missing_token_403(self):
        r = client.post("/api/tutoring/subject-classify", json={"content": "鸡兔同笼"})
        assert r.status_code == 403

    def test_invalid_token_403(self):
        r = client.post(
            "/api/tutoring/subject-classify",
            json={"content": "鸡兔同笼"},
            headers={"x-internal-token": "wrong_token"},
        )
        assert r.status_code == 403

    def test_all_empty_params_422(self):
        """content 与 image_url 均为空 → 422 参数校验"""
        r = client.post(
            "/api/tutoring/subject-classify",
            json={"content": None, "image_url": None},
            headers=AUTH,
        )
        assert r.status_code == 422

    def test_normal_math(self, mock_classify):
        mock_classify("math")
        r = client.post(
            "/api/tutoring/subject-classify",
            json={"content": "鸡兔同笼，共35头94脚，各几只？", "image_url": None},
            headers=AUTH,
        )
        assert r.status_code == 200
        assert r.json() == {"subject": "math"}

    def test_normal_physics(self, mock_classify):
        mock_classify("physics")
        r = client.post(
            "/api/tutoring/subject-classify",
            json={"content": None, "image_url": "https://cos-xxx/1.jpg"},
            headers=AUTH,
        )
        assert r.status_code == 200
        assert r.json() == {"subject": "physics"}

    def test_failure_empty_subject(self, mock_classify):
        """分类失败 → 200 + subject=null(不 5xx,Java 按 math 放行)"""
        mock_classify(None)
        r = client.post(
            "/api/tutoring/subject-classify",
            json={"content": "任意题"},
            headers=AUTH,
        )
        assert r.status_code == 200
        assert r.json() == {"subject": None}
