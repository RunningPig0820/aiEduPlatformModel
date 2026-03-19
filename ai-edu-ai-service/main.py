"""
AI服务启动入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Education Platform - AI Service",
    description="AI微服务：OCR、大模型、RAG检索",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-service"}


# 注册路由
# from api import ocr, llm, rag
# app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
# app.include_router(llm.router, prefix="/api/llm", tags=["LLM"])
# app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)