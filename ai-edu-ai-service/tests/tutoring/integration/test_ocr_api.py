"""
任务 7.2: /api/ocr/recognize 端点集成测试

403(缺 token)/ 400(非图片)/ 200(识别成功)/ 500(识别失败)
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest
from fastapi.testclient import TestClient

from config.settings import settings


@pytest.fixture(scope="module")
def client():
    from main import app

    return TestClient(app)


def _headers(token=None):
    token = token if token is not None else settings.INTERNAL_TOKEN
    return {"x-internal-token": token}


class TestOCRRecognizeEndpoint:
    """POST /api/ocr/recognize"""

    def test_missing_token_403(self, client):
        r = client.post("/api/ocr/recognize", files={"file": ("q.jpg", b"img", "image/jpeg")})
        assert r.status_code == 403

    def test_invalid_image_400(self, client):
        """非图片文件 → 400"""
        r = client.post(
            "/api/ocr/recognize",
            files={"file": ("a.txt", b"hello", "text/plain")},
            headers=_headers(),
        )
        assert r.status_code == 400

    def test_valid_returns_text_and_confidence(self, client, monkeypatch):
        monkeypatch.setattr(
            "api.ocr.ocr_service.recognize",
            lambda img: {"text": "鸡兔同笼，共35头94脚，各几只？", "confidence": 0.92},
        )
        r = client.post(
            "/api/ocr/recognize",
            files={"file": ("q.jpg", b"fake-img", "image/jpeg")},
            headers=_headers(),
        )
        assert r.status_code == 200
        assert r.json()["text"] == "鸡兔同笼，共35头94脚，各几只？"
        assert r.json()["confidence"] == 0.92

    def test_ocr_failure_500(self, client, monkeypatch):
        def fail(img):
            raise RuntimeError("baidu down")

        monkeypatch.setattr("api.ocr.ocr_service.recognize", fail)
        r = client.post(
            "/api/ocr/recognize",
            files={"file": ("q.jpg", b"fake-img", "image/jpeg")},
            headers=_headers(),
        )
        assert r.status_code == 500
