"""
AI Work Assistant - Main Application Entry Point

Personal AI Work Assistant System for enterprise technical professionals.
Reduces daily work time through automated content generation.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import get_settings
from app.api.knowledge import router as knowledge_router
from app.api.scenarios import router as scenario_router
from app.api.health import router as health_router

# =============================================================================
# Logging
# =============================================================================

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger("ai_work_assistant")


# =============================================================================
# Application Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("AI Work Assistant starting...")
    logger.info(f"  LLM Model: {settings.llm_model}")
    logger.info(f"  Embedding Model: {settings.embedding_model}")
    logger.info(f"  ChromaDB Path: {settings.chroma_persist_dir}")
    logger.info(f"  OpenAI Configured: {bool(settings.openai_api_key)}")
    logger.info("=" * 60)

    # Initialize vector store on startup
    try:
        from app.knowledge.vector_store import get_vector_store
        store = get_vector_store()
        logger.info(f"Vector store ready. {store.count()} documents loaded.")
    except Exception as e:
        logger.warning(f"Vector store initialization warning: {e}")

    yield

    # Shutdown
    logger.info("AI Work Assistant shutting down...")


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AI Work Assistant",
    description="""
## 个人工作效率AI系统

面向企业技术岗位人员的智能工作助手，帮助减少：
- 认知负担
- 准备时间
- 重复性写作
- 信息查找时间
- 技术解释时间
- 汇报和文档编写时间

### 场景模块
- **技术问题排查** - 快速分析故障并提供排查方案
- **技术问题回答** - 准确回答技术问题
- **客户答复** - 生成专业的客户沟通回复
- **周报生成** - 自动生成结构化周报
- **汇报生成** - 准备汇报和PPT材料
- **培训生成** - 生成培训课程内容
- **演示准备** - 准备产品演示方案
- **PoC支持** - 制定PoC方案
- **问题升级** - 整理问题升级材料

### 输出模式
- **客户模式** - 适合对外沟通
- **技术模式** - 详细技术说明
- **领导模式** - 简洁管理汇总
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# Register Routers
# =============================================================================

app.include_router(health_router)
app.include_router(knowledge_router)
app.include_router(scenario_router)


# =============================================================================
# Web Frontend — Static Files & UI Route
# =============================================================================

WEB_DIR = Path(__file__).resolve().parent / "web"

if WEB_DIR.is_dir():
    @app.get("/ui", include_in_schema=False)
    @app.get("/", include_in_schema=False)
    async def serve_ui():
        """Serve the web frontend SPA."""
        return FileResponse(WEB_DIR / "index.html")

    # Mount static assets (CSS, JS, images) at /static
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

    logger.info(f"Web frontend enabled — serving from {WEB_DIR}")
else:
    logger.warning(f"Web directory not found at {WEB_DIR} — frontend disabled")


# =============================================================================
# Run with: python main.py
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level=settings.log_level.lower(),
    )
