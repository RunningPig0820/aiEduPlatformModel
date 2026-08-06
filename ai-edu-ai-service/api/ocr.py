"""
OCR API路由 - 拍照识别题目

POST /api/ocr/recognize: 图片上传 → 识别题目文本 → 供前端确认/修改
(需 x-internal-token; 图片 jpg/png/webp/bmp; 上限 5MB)

对齐: openspec/changes/ai-tutoring/api.md(OCR 端点契约)
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Header

from api.chat import verify_internal_token
from core.ocr_service import ocr_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["OCR"])

_ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
_MAX_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/recognize")
async def recognize_image(
    file: UploadFile = File(...),
    x_internal_token: str = Header(None),
):
    """识别图片中的题目文字,返回 text + confidence(前端确认/修改后进答疑)"""
    verify_internal_token(x_internal_token)

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="无效图片: 仅支持 jpg/png/webp/bmp")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="无效图片: 空文件")
    if len(image_bytes) > _MAX_SIZE:
        raise HTTPException(status_code=400, detail="无效图片: 超过 5MB 上限")

    try:
        result = ocr_service.recognize(image_bytes)
    except Exception as e:
        logger.error("OCR recognize failed: %s", e)
        raise HTTPException(status_code=500, detail="OCR 识别失败")

    return {"text": result["text"], "confidence": result["confidence"]}


@router.post("/recognize-batch")
async def recognize_batch(
    files: List[UploadFile] = File(...),
    x_internal_token: str = Header(None),
):
    """批量识别(兼容旧 stub)"""
    verify_internal_token(x_internal_token)
    results = []
    for file in files:
        image_bytes = await file.read()
        try:
            result = ocr_service.recognize(image_bytes)
            results.append({
                "filename": file.filename,
                "text": result["text"],
                "confidence": result["confidence"],
            })
        except Exception as e:
            logger.error("OCR batch item failed: %s", e)
            results.append({"filename": file.filename, "text": "", "confidence": 0.0})
    return {"results": results}
