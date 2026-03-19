# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Education Platform microservice - a Python FastAPI service providing OCR, LLM chat, and RAG capabilities for an education platform. The project integrates with a Java backend service and uses RabbitMQ for async homework grading tasks.

## Commands

```bash
# Install dependencies
pip install -r ai-edu-ai-service/requirements.txt

# Run the development server
cd ai-edu-ai-service && python main.py
# Or with uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest

# Run specific test file
pytest tests/test_file.py -v
```

## Architecture

```
ai-edu-ai-service/
├── main.py              # FastAPI app entry point, CORS config, health check
├── requirements.txt     # Python dependencies
├── api/                 # API route handlers (thin layer)
│   ├── ocr.py           # POST /recognize, /recognize-batch
│   ├── llm.py           # POST /chat, /grade
│   └── rag.py           # POST /search, /embed
├── core/                # Business logic and external integrations
│   ├── ocr_service.py   # PaddleOCR wrapper
│   ├── llm_service.py   # LangChain + Dashscope (通义千问)
│   └── emotion_service.py # Emotion detection for adaptive responses
└── mq/                  # Message queue consumers
    └── homework_consumer.py # RabbitMQ consumer for homework grading workflow
```

**Three-layer pattern:** API routes handle HTTP, core services contain business logic, mq handles async tasks from Java backend.

## Key Integrations

- **LLM**: LangChain framework with Dashscope SDK (阿里通义千问/Qwen)
- **OCR**: PaddleOCR + PaddlePaddle
- **Vector DB**: Milvus for RAG similarity search
- **Message Queue**: RabbitMQ (pika) for async homework processing

## Development Notes

- The routes in main.py are currently commented out - uncomment as implementations are completed
- Services use singleton pattern (e.g., `llm_service = LLMService()`)
- All endpoint implementations are currently stubs (TODO) - this is early-stage code
- Homework grading workflow: RabbitMQ message → OCR → LLM grading → callback to Java service