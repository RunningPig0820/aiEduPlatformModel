"""
OCR API路由
"""
from fastapi import APIRouter, UploadFile, File
from typing import List

router = APIRouter()


@router.post("/recognize")
async def recognize_image(file: UploadFile = File(...)):
    """
    识别图片中的文字
    """
    # TODO: 实现OCR识别
    return {
        "success": True,
        "text": "识别结果",
        "confidence": 0.95
    }


@router.post("/recognize-batch")
async def recognize_batch(files: List[UploadFile] = File(...)):
    """
    批量识别图片
    """
    results = []
    for file in files:
        results.append({
            "filename": file.filename,
            "text": "识别结果",
            "confidence": 0.95
        })
    return {"results": results}