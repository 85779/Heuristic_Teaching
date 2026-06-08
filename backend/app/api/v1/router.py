"""
API v1 路由汇总
"""

from fastapi import APIRouter

api_router = APIRouter()

# 注册各模块路由
from app.modules.solving.routes import router as solving_router
from app.modules.intervention.routes import router as intervention_router
from app.modules.recommendation.routes import router as recommendation_router

api_router.include_router(solving_router, tags=["solving"])
api_router.include_router(intervention_router, tags=["intervention"])
api_router.include_router(recommendation_router, tags=["recommendation"])

# student_model routes (no external dependencies)
from app.modules.student_model.routes import router as student_model_router
api_router.include_router(student_model_router, tags=["student-model"])

# teaching routes (depends on student_model)
from app.modules.teaching.routes import router as teaching_router
api_router.include_router(teaching_router, tags=["teaching"])

# knowledge_base requires chromadb (optional dependency)
try:
    from app.modules.knowledge_base.routes import router as knowledge_base_router
    api_router.include_router(knowledge_base_router, tags=["knowledge-base"])
except ImportError:
    pass


@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": "v1"}