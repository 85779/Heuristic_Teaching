"""
FastAPI 应用入口
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.api.v1.router import api_router
from app.core.registry.module_registry import ModuleRegistry
from app.core.events.event_bus import EventBus
from app.infrastructure.database.mongodb import get_mongodb

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Math Tutor API...")
    mongodb = get_mongodb()
    try:
        await mongodb.connect()
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.warning(f"MongoDB connection failed (continuing without persistence): {e}")
    yield
    # Shutdown
    logger.info("Shutting down Math Tutor API...")
    mongodb = get_mongodb()
    try:
        await mongodb.disconnect()
        logger.info("MongoDB disconnected")
    except Exception as e:
        logger.warning(f"MongoDB disconnection error: {e}")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="Math Tutor API",
        description="高中数学教辅系统",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=lifespan,
    )
    
    # 注册 API 路由
    app.include_router(api_router, prefix="/api/v1")
    
    return app


app = create_app()