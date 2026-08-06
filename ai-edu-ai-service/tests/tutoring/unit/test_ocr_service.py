"""
任务 7.1: core/ocr_service.py 测试

百度 OCR REST 流程(mock httpx.post):
token 获取(缓存)→ general_basic 识别 → text/confidence
"""
import sys
import os

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)

import pytest


class _FakeResp:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def json(self):
        return self._payload


class TestOCRService:
    """百度 OCR 服务"""

    def _patch_http(self, monkeypatch, token_payload=None, ocr_payload=None):
        """把 httpx.post 换成假实现,记录调用 URL"""
        calls = []
        token_payload = token_payload or {"access_token": "tok", "expires_in": 3600}
        ocr_payload = ocr_payload or {
            "words_result": [
                {"words": "鸡兔同笼，共35头94脚", "probability": {"average": 0.93}},
            ],
            "words_result_num": 1,
        }

        def fake_post(url, **kwargs):
            calls.append(url)
            if "oauth" in url:
                return _FakeResp(token_payload)
            return _FakeResp(ocr_payload)

        monkeypatch.setattr("core.ocr_service.httpx.post", fake_post)
        return calls

    def test_recognize_returns_text_and_confidence(self, monkeypatch):
        from core.ocr_service import OCRService

        calls = self._patch_http(monkeypatch)
        svc = OCRService(api_key="k", secret_key="s")

        result = svc.recognize(b"fake-image")

        assert result["text"] == "鸡兔同笼，共35头94脚"
        assert result["confidence"] == 0.93
        assert any("oauth" in u for u in calls)
        assert any("general_basic" in u for u in calls)

    def test_token_cached_across_calls(self, monkeypatch):
        """access_token 只取一次,后续复用缓存"""
        from core.ocr_service import OCRService

        calls = self._patch_http(monkeypatch)
        svc = OCRService(api_key="k", secret_key="s")

        svc.recognize(b"img1")
        svc.recognize(b"img2")

        assert sum(1 for u in calls if "oauth" in u) == 1

    def test_multiline_text_joined(self, monkeypatch):
        from core.ocr_service import OCRService

        self._patch_http(monkeypatch, ocr_payload={
            "words_result": [
                {"words": "第一行", "probability": {"average": 0.9}},
                {"words": "第二行", "probability": {"average": 0.8}},
            ],
            "words_result_num": 2,
        })
        svc = OCRService(api_key="k", secret_key="s")

        result = svc.recognize(b"img")

        assert result["text"] == "第一行\n第二行"
        assert result["confidence"] == pytest.approx(0.85)

    def test_ocr_error_code_raises(self, monkeypatch):
        from core.ocr_service import OCRService

        self._patch_http(monkeypatch, ocr_payload={"error_code": 17, "error_msg": "limit reached"})
        svc = OCRService(api_key="k", secret_key="s")

        with pytest.raises(RuntimeError):
            svc.recognize(b"img")

    def test_token_fetch_failure_raises(self, monkeypatch):
        from core.ocr_service import OCRService

        self._patch_http(monkeypatch, token_payload={"error_description": "invalid client"})
        svc = OCRService(api_key="k", secret_key="s")

        with pytest.raises(RuntimeError):
            svc.recognize(b"img")
