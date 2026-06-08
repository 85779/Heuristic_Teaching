"""Tests for KnowledgeAnchorRetriever."""

import pytest
from app.modules.recommendation.models import (
    AnchorType,
    StudentProfile,
    TriggerOutcome,
)


class TestKnowledgeAnchorRetriever:
    """Test suite for KnowledgeAnchorRetriever."""

    @pytest.mark.asyncio
    async def test_same_kp_anchor_when_r_dominant(self, anchor_retriever):
        """R-type (ratio > 0.65) returns SAME_KP anchor."""
        profile = StudentProfile(
            student_id="test_student",
            dimension_ratio=0.75,
            recent_problems=[],
            weak_kps=["KP_2_01"],
            mastered_kps=["KP_1_01"],
            recent_methods=[],
        )
        anchor = await anchor_retriever.retrieve(
            profile=profile,
            current_kps=["KP_3_13"],
            current_method="配方法",
        )
        assert anchor.anchor_type == AnchorType.SAME_KP
        assert len(anchor.target_kps) > 0
        assert anchor.generation_goal != ""

    @pytest.mark.asyncio
    async def test_variation_anchor_when_m_dominant(self, anchor_retriever):
        """M-type (ratio < 0.35) returns VARIATION anchor."""
        # KP_1_01 has related_types=["类型Ⅰ"] which maps to type_kp_mapping
        profile = StudentProfile(
            student_id="test_student",
            dimension_ratio=0.25,
            recent_problems=[],
            weak_kps=[],
            mastered_kps=["KP_1_01"],
            recent_methods=["待定系数法"],
        )
        anchor = await anchor_retriever.retrieve(
            profile=profile,
            current_kps=["KP_1_01"],
            current_method="数形结合",
        )
        assert anchor.anchor_type == AnchorType.VARIATION
        assert len(anchor.target_kps) > 0

    @pytest.mark.asyncio
    async def test_balanced_anchor_when_mixed(self, anchor_retriever):
        """Balanced (0.35 <= ratio <= 0.65) returns BALANCED anchor."""
        profile = StudentProfile(
            student_id="test_student",
            dimension_ratio=0.5,
            recent_problems=[],
            weak_kps=["KP_2_01", "KP_3_01"],
            mastered_kps=[],
            recent_methods=[],
        )
        anchor = await anchor_retriever.retrieve(
            profile=profile,
            current_kps=["KP_3_13"],
            current_method="配方法",
        )
        assert anchor.anchor_type == AnchorType.BALANCED
        assert anchor.generation_goal != ""

    @pytest.mark.asyncio
    async def test_exclude_recent_methods_for_variation(self, anchor_retriever):
        """Variation anchor excludes recently used methods."""
        profile = StudentProfile(
            student_id="test_student",
            dimension_ratio=0.20,  # M-type
            recent_problems=[],
            weak_kps=[],
            mastered_kps=[],
            recent_methods=["配方法", "换元法"],
        )
        anchor = await anchor_retriever.retrieve(
            profile=profile,
            current_kps=["KP_3_13"],
            current_method=None,
        )
        # Should exclude recent methods
        for excluded in profile.recent_methods:
            for kp in anchor.target_kps:
                assert excluded not in kp.methods

    @pytest.mark.asyncio
    async def test_same_kp_uses_prerequisites(self, anchor_retriever, kb_api):
        """SAME_KP anchor uses prerequisite KPs."""
        profile = StudentProfile(
            student_id="test_student",
            dimension_ratio=0.80,  # R-type
            recent_problems=[],
            weak_kps=[],
            mastered_kps=[],
            recent_methods=[],
        )
        # Get prerequisites for a known KP
        prereqs = await kb_api.get_prerequisites("KP_3_13")
        anchor = await anchor_retriever.retrieve(
            profile=profile,
            current_kps=["KP_3_13"],
            current_method=None,
        )
        # If there were prerequisites, anchor should include them
        # (not already mastered)
        if prereqs:
            assert len(anchor.target_kps) > 0