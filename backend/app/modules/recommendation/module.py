"""Recommendation module implementation.

This module generates personalized math problem recommendations
based on student profiles and knowledge base anchors.
"""

import os
from app.core.interfaces.module import IModule
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
    from app.core.context import ModuleContext

from app.modules.recommendation.knowledge_base.knowledge_api import KnowledgeBaseAPI
from app.modules.recommendation.retriever.knowledge_anchor_retriever import KnowledgeAnchorRetriever
from app.modules.recommendation.generator.problem_generator import ProblemGenerator
from app.modules.recommendation.generator.prompt_templates import ProblemPromptTemplates
from app.modules.recommendation.generator.problem_validator import ProblemValidator
from app.modules.recommendation.generator.fallback_generator import FallbackGenerator
from app.modules.recommendation.scorer.difficulty_scorer import DifficultyScorer
from app.modules.recommendation.service import RecommendationService
from app.infrastructure.llm.dashscope_client import DashScopeClient


class RecommendationModule(IModule):
    """Recommendation module for personalized problem generation."""

    @property
    def module_id(self) -> str:
        """Unique module identifier."""
        return "recommendation"

    @property
    def module_name(self) -> str:
        """Module display name."""
        return "Recommendation Module"

    @property
    def version(self) -> str:
        """Module version."""
        return "1.0.0"

    @property
    def dependencies(self) -> list[str]:
        """List of module IDs this module depends on."""
        return ["solving"]

    @property
    def provides_events(self) -> list[str]:
        """List of event types this module publishes."""
        return ["recommendation.generated"]

    @property
    def subscribes_events(self) -> list[str]:
        """List of event types this module subscribes to."""
        return []

    async def initialize(self, context: "ModuleContext") -> None:
        """Initialize the recommendation module.
        
        Creates and wires up all components:
        - KnowledgeBaseAPI (reads knowledge ontology)
        - DashScopeClient (LLM for generation)
        - KnowledgeAnchorRetriever (profile-based retrieval)
        - ProblemGenerator (LLM generation)
        - FallbackGenerator (fallback when LLM fails)
        - DifficultyScorer (difficulty calculation)
        - RecommendationService (main orchestrator)
        """
        self._context = context
        self._logger = context.logger

        # Initialize components
        kb_api = KnowledgeBaseAPI(
            kb_dir="data/knowledge_ontology"
        )

        api_key = context.get_config("DASHSCOPE_API_KEY", "") or os.environ.get("DASHSCOPE_API_KEY", "")
        llm_client = DashScopeClient(
            api_key=api_key,
            model=context.get_config("RECOMMENDATION_MODEL", "qwen-turbo"),
        )

        anchor_retriever = KnowledgeAnchorRetriever(kb_api=kb_api)
        fallback_generator = FallbackGenerator()
        difficulty_scorer = DifficultyScorer()
        prompt_templates = ProblemPromptTemplates()
        problem_validator = ProblemValidator()
        problem_generator = ProblemGenerator(
            llm_client=llm_client,
            prompt_templates=prompt_templates,
            validator=problem_validator,
            model=context.get_config("RECOMMENDATION_MODEL", "qwen-turbo"),
        )

        # Get ProfileManager from Module 4 if available
        profile_manager = None
        try:
            student_module = context.registry.get_module("student_model")
            if student_module and hasattr(student_module, "_service"):
                profile_manager = student_module._service
        except Exception:
            pass

        # Create main service
        self._service = RecommendationService(
            kb_api=kb_api,
            anchor_retriever=anchor_retriever,
            generator=problem_generator,
            fallback=fallback_generator,
            difficulty_scorer=difficulty_scorer,
            llm_client=llm_client,
            profile_manager=profile_manager,
        )

        # Wire service to routes
        from . import routes as recommendation_routes
        recommendation_routes.set_module(self)

        self._logger.info("RecommendationModule initialized")

    async def shutdown(self) -> None:
        """Shutdown the recommendation module."""
        if hasattr(self, '_context') and self._context:
            self._logger = getattr(self, '_logger', None)
            if self._logger:
                self._logger.info("RecommendationModule shutting down")

    def register_routes(self, router: "APIRouter") -> None:
        """Register API routes for the recommendation module."""
        from . import routes as recommendation_routes
        recommendation_routes.set_module(self)
        router.include_router(recommendation_routes.router)