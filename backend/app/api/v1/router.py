"""
API v1 路由汇总
"""

from fastapi import APIRouter

api_router = APIRouter()

# TODO: 注册各模块路由
# from app.modules.solving.routes import router as solving_router
# from app.modules.intervention.routes import router as intervention_router
# api_router.include_router(solving_router, prefix="/solving", tags=["solving"])
# api_router.include_router(intervention_router, prefix="/intervention", tags=["intervention"])


@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": "v1"}