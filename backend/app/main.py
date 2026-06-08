"""
FastAPI 应用入口
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import settings
from app.api.v1.router import api_router
from app.core.context import ModuleContext
from app.core.events.event_bus import EventBus
from app.core.registry.module_registry import ModuleRegistry
from app.core.state.session_manager import SessionManager
from app.core.state.state_manager import StateManager
from app.infrastructure.database.mongodb import get_mongodb
from app.modules.solving.module import SolvingModule
from app.modules.intervention.module import InterventionModule
from app.modules.recommendation.module import RecommendationModule
from app.modules.student_model.module import StudentModelModule
from app.modules.teaching.module import TeachingModule

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # ===== Startup =====
    logger.info("Starting Math Tutor API...")

    # MongoDB with short timeout
    mongodb = get_mongodb()
    try:
        await mongodb.connect(serverSelectionTimeoutMS=3000)
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.warning(f"MongoDB unavailable (continuing without persistence): {e}")

    # Core infrastructure
    event_bus = EventBus()
    session_manager = SessionManager()
    state_manager = StateManager()
    registry = ModuleRegistry(event_bus=event_bus)

    # Build module context
    context = ModuleContext(
        registry=registry,
        orchestrator=None,       # Not used — modules call DashScopeClient directly
        state_manager=state_manager,
        session_manager=session_manager,
        event_bus=event_bus,
        config=settings,
        repository=None,         # Not used — modules manage their own repositories
        logger=logging.getLogger("socrates.module"),
    )

    # Register and initialize modules in dependency order
    solving = SolvingModule()
    intervention = InterventionModule()
    recommendation = RecommendationModule()
    student_model = StudentModelModule()
    teaching = TeachingModule()

    registry.register_module(solving)
    registry.register_module(intervention)
    registry.register_module(recommendation)
    registry.register_module(student_model)
    registry.register_module(teaching)

    try:
        await registry.initialize_all(context)
        logger.info(f"Modules initialized: {registry.list_modules()}")
    except Exception as e:
        logger.error(f"Module initialization failed: {e}")
        raise

    # Initialize global dependencies
    from app.api import dependencies
    dependencies.init_dependencies(registry, session_manager)

    app.state.event_bus = event_bus
    app.state.session_manager = session_manager
    app.state.state_manager = state_manager

    yield

    # ===== Shutdown =====
    logger.info("Shutting down Math Tutor API...")
    try:
        await registry.shutdown_all()
    except Exception as e:
        logger.warning(f"Module shutdown error: {e}")
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
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
