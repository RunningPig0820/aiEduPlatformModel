"""
AI服务启动入口
"""
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to sys.path for edukg module
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def validate_kg_config():
    """
    Validate Knowledge Graph configuration on startup.

    Raises:
        SystemExit: If required configuration is missing
    """
    errors = []
    warnings = []

    # Check Neo4j configuration
    neo4j_uri = os.getenv("NEO4J_URI", "")
    neo4j_user = os.getenv("NEO4J_USER", "")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")

    if not neo4j_uri:
        errors.append("NEO4J_URI is not set")
    elif not neo4j_uri.startswith("bolt://"):
        warnings.append(f"NEO4J_URI should start with 'bolt://', got: {neo4j_uri}")

    if not neo4j_user:
        errors.append("NEO4J_USER is not set")

    if not neo4j_password:
        errors.append("NEO4J_PASSWORD is not set")

    # Check if entity data directory exists
    entity_dir = os.path.join(
        os.path.dirname(__file__),
        "data", "edukg", "entities"
    )
    if not os.path.exists(entity_dir):
        warnings.append(f"Entity data directory not found: {entity_dir}")

    # Print validation results
    if warnings:
        print("\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"   - {warning}")

    if errors:
        print("\n❌ Configuration Errors:")
        for error in errors:
            print(f"   - {error}")
        print("\nKnowledge Graph features will be disabled.")
        print("Please set the required environment variables in .env file.")
        return False

    return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    from edukg.core.neo4j import init_neo4j, close_neo4j
    from edukg.core.kg.entity_linker import init_entity_linker

    print("\n" + "=" * 50)
    print("AI Education Platform - AI Service")
    print("=" * 50)

    # Validate configuration
    kg_config_valid = validate_kg_config()

    print("\nInitializing Knowledge Graph services...")
    if kg_config_valid:
        try:
            init_neo4j()
            init_entity_linker()
            print("✓ Knowledge Graph services initialized successfully")
        except Exception as e:
            print(f"✗ Failed to initialize KG services: {e}")
            print("  Knowledge Graph features will be disabled.")
    else:
        print("⚠ Skipping KG initialization due to configuration errors.")

    print("\n" + "=" * 50 + "\n")

    yield

    # Shutdown
    print("\nShutting down Knowledge Graph services...")
    close_neo4j()
    print("Knowledge Graph services closed")


app = FastAPI(
    title="AI Education Platform - AI Service",
    description="AI微服务：OCR、大模型、RAG检索、知识图谱",
    version="1.0.0",
    lifespan=lifespan
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
from api.chat import router as chat_router
from api.kg import router as kg_router
from api.neo4j import router as neo4j_router

app.include_router(chat_router)
app.include_router(kg_router)
app.include_router(neo4j_router)

# 后续注册其他路由
# from api import ocr, rag
# app.include_router(ocr.router, prefix="/api/ocr", tags=["OCR"])
# app.include_router(rag.router, prefix="/api/rag", tags=["RAG"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=9527, reload=True)