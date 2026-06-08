"""Modules layer - Business logic modules."""

from app.modules.solving import SolvingModule
from app.modules.intervention import InterventionModule
from app.modules.recommendation import RecommendationModule
from app.modules.student_model import StudentModelModule
from app.modules.teaching import TeachingModule

# knowledge_base requires chromadb (optional heavy dependency)
try:
    from app.modules.knowledge_base import RAGService
except ImportError:
    RAGService = None  # type: ignore

__all__ = [
    "SolvingModule",
    "InterventionModule",
    "RecommendationModule",
    "StudentModelModule",
    "TeachingModule",
    "RAGService",
]