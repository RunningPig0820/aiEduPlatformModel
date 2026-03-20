# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Education Platform microservice - a Python FastAPI service providing LLM Gateway capabilities for an education platform. The project integrates with a Java backend service and supports multiple LLM providers (智谱, DeepSeek, 阿里百炼).

## Commands

```bash
# Install dependencies
pip install -r ai-edu-ai-service/requirements.txt

# Run the development server
cd ai-edu-ai-service && python main.py
# Or with uvicorn directly:
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest ai-edu-ai-service/tests/

# Run specific test file
pytest ai-edu-ai-service/tests/test_factory.py -v
```

## Architecture

```
ai-edu-ai-service/
├── main.py              # FastAPI app entry point
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
│
├── config/              # Configuration
│   ├── settings.py      # Pydantic Settings (API Keys from env)
│   └── model_config.py  # Model configurations and scene mappings
│
├── api/                 # API route handlers
│   └── chat.py          # POST /api/llm/chat, /api/llm/chat/stream, GET /api/llm/models
│
├── core/                # Business logic
│   ├── gateway/         # LLM Gateway
│   │   ├── factory.py   # LLM Factory (creates LangChain ChatModel instances)
│   │   └── router.py    # Model Router (scene → model mapping)
│   └── tools/           # Tool definitions (for bind_tools)
│
└── models/              # Pydantic data models
    └── chat.py          # ChatRequest, ChatResponse, etc.

tests/                   # Test files
├── test_factory.py      # LLM Factory tests
├── test_zhipu.py        # 智谱 integration tests
├── test_deepseek.py     # DeepSeek integration tests
├── test_bailian.py      # 百炼 integration tests
├── test_router.py       # Model Router tests
└── test_chat_api.py     # API endpoint tests
```

## LLM Gateway Architecture

```
┌─────────────┐      JWT Token      ┌─────────────┐     内部Token     ┌─────────────────┐
│    前端      │ ─────────────────▶ │  Java 后端   │ ───────────────▶ │   Python AI     │
└─────────────┘                     │             │                   │     服务        │
                                    │  权限验证    │                   └────────┬────────┘
                                    │  用户管理    │                            │
                                    └─────────────┘                            ▼
                                                          ┌─────────────────────────────────┐
                                                          │         LLM Gateway             │
                                                          │  ┌─────────────┐                │
                                                          │  │Model Router │                │
                                                          │  │scene→model  │                │
                                                          │  └──────┬──────┘                │
                                                          │         │                       │
                                                          │         ▼                       │
                                                          │  ┌─────────────┐                │
                                                          │  │LLM Factory  │                │
                                                          │  └──────┬──────┘                │
                                                          │         │                       │
                                                          │    ┌────┴────┐                   │
                                                          │    ▼    ▼    ▼                   │
                                                          │ ChatZhipuAI ChatOpenAI ChatTongyi│
                                                          └─────────────────────────────────┘
```

### Key Components

1. **LLM Factory** (`core/gateway/factory.py`)
   - Creates LangChain ChatModel instances
   - Supports: 智谱 (ChatZhipuAI), DeepSeek (ChatOpenAI compatible), 百炼 (ChatTongyi)
   - API Keys loaded from environment variables

2. **Model Router** (`core/gateway/router.py`)
   - Scene-driven routing: `scene → (provider, model)`
   - Free model priority (glm-4-flash for most scenes)
   - Default fallback

3. **Configuration** (`config/`)
   - `settings.py`: Pydantic Settings for API Keys
   - `model_config.py`: Model metadata and scene mappings

## Supported LLM Providers

| Provider | Models | Free | Tools | Vision |
|----------|--------|------|-------|--------|
| 智谱 | glm-4-flash | ✓ | ✓ | - |
| 智谱 | glm-4.5-air | - | ✓ | - |
| 智谱 | glm-4.6v | - | ✓ | ✓ |
| 智谱 | glm-4.7 | - | ✓ | - |
| DeepSeek | deepseek-chat | - | ✓ | - |
| DeepSeek | deepseek-coder | - | ✓ | - |
| 百炼 | qwen-turbo | - | ✓ | - |
| 百炼 | qwen-plus | - | ✓ | - |

## Scene → Model Mapping

| Scene | Provider | Model | Notes |
|-------|----------|-------|-------|
| page_assistant | zhipu | glm-4-flash | Free! |
| faq | zhipu | glm-4-flash | Free! |
| homework_grading | deepseek | deepseek-chat | Needs deep understanding |
| image_analysis | zhipu | glm-4.6v | Vision model |
| content_generation | deepseek | deepseek-chat | Complex task |

## Security

- **API Keys**: Stored in environment variables, never in code
- **`.env`**: Added to `.gitignore`, never committed
- **`.env.example`**: Template without real values
- **Internal Token**: Java backend must provide `x-internal-token` header

## Key Integrations

- **LLM**: LangChain framework with multiple providers
  - langchain-community (ChatZhipuAI, ChatTongyi)
  - langchain-openai (ChatOpenAI for DeepSeek)
- **OCR**: PaddleOCR + PaddlePaddle (future)
- **Vector DB**: Milvus for RAG (future)
- **MCP**: Model Context Protocol client for Java backend (future)