"""
FastAPI 应用入口
"""

from fastapi import FastAPI
from app.config import settings
from app.api.v1.router import api_router
from app.core.registry.module_registry import ModuleRegistry
from app.core.events.event_bus import EventBus


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title="Math Tutor API",
        description="高中数学教辅系统",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    
    # 注册 API 路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 应用启动事件
    @app.on_event("startup")
    async def startup_event():
        # TODO: 初始化模块注册器
        # TODO: 初始化事件总线
        pass
    
    # 应用关闭事件
    @app.on_event("shutdown")
    async def shutdown_event():
        # TODO: 关闭所有模块
        pass
    
    return app


app = create_app()