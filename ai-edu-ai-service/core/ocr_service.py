"""
OCR服务封装 - 百度 OCR REST API

实现说明: 用 OAuth access_token + general_basic 接口,只需 BAIDU_OCR_API_KEY / SECRET_KEY。
baidu-aip 的 AipOcr 需要 APP_ID 而当前 env 只有 API_KEY+SECRET_KEY,故直接用 httpx
走百度标准流程(token → OCR),返回 text/confidence。

对齐: openspec/changes/ai-tutoring/api.md(OCR 端点)/design.md 决策 11(拍题 OCR 前置)
"""
import base64
import logging
import time

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

_OAUTH_URL = "https://aip.baidubce.com/oauth/2.0/token"
_OCR_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"


class OCRService:
    """百度 OCR 服务封装(无状态 + access_token 缓存)"""

    def __init__(self, api_key: str = None, secret_key: str = None, timeout: float = 15.0):
        self.api_key = api_key or settings.BAIDU_OCR_API_KEY
        self.secret_key = secret_key or settings.BAIDU_OCR_SECRET_KEY
        self.timeout = timeout
        self._token: str = ""
        self._token_expire_at: float = 0.0

    def _get_access_token(self) -> str:
        """获取(或复用未过期的缓存)access_token"""
        if self._token and time.time() < self._token_expire_at:
            return self._token

        resp = httpx.post(
            _OAUTH_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key,
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"百度 OAuth 获取 token 失败: {data.get('error_description', data)}")

        self._token = token
        # 提前 60s 过期,避免边界命中失效 token
        self._token_expire_at = time.time() + int(data.get("expires_in", 2592000)) - 60
        return token

    def recognize(self, image_bytes: bytes) -> dict:
        """识别图片文字,返回 {"text", "confidence"}。

        Args:
            image_bytes: 图片原始字节(jpg/png 等)

        Raises:
            RuntimeError: token 获取失败 / OCR 调用失败(带 error_code)
        """
        token = self._get_access_token()
        image_b64 = base64.b64encode(image_bytes).decode()

        resp = httpx.post(
            _OCR_URL,
            params={"access_token": token},
            data={"image": image_b64, "probability": "true"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("error_code"):
            raise RuntimeError(
                f"百度 OCR 失败: {data['error_code']} {data.get('error_msg', '')}"
            )

        words_result = data.get("words_result", [])
        text = "\n".join(w["words"] for w in words_result)
        probs = [
            w.get("probability", {}).get("average")
            for w in words_result
        ]
        probs = [p for p in probs if p is not None]
        confidence = round(sum(probs) / len(probs), 4) if probs else 0.0

        return {"text": text, "confidence": confidence}


# 单例
ocr_service = OCRService()
