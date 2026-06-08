"""Tests for KnowledgeBaseAPI."""

import pytest
from app.modules.recommendation.knowledge_base.knowledge_api import KnowledgeBaseAPI


class TestKnowledgeBaseAPI:
    """Test suite for KnowledgeBaseAPI."""

    @pytest.mark.asyncio
    async def test_load_kps(self, kb_api):
        """Knowledge points are loaded on initialization."""
        kp = await kb_api.get_kp("KP_1_01")
        assert kp is not None
        assert "kp_id" in kp
        assert "name" in kp

    @pytest.mark.asyncio
    async def test_get_nonexistent_kp(self, kb_api):
        """Non-existent KP returns None."""
        kp = await kb_api.get_kp("KP_NONEXISTENT")
        assert kp is None

    @pytest.mark.asyncio
    async def test_get_kps_multiple(self, kb_api):
        """Multiple KPs can be retrieved."""
        kps = await kb_api.get_kps(["KP_1_01", "KP_2_01"])
        assert len(kps) == 2
        assert all("kp_id" in kp for kp in kps)

    @pytest.mark.asyncio
    async def test_get_prerequisites(self, kb_api):
        """Prerequisites are retrieved correctly."""
        prereqs = await kb_api.get_prerequisites("KP_3_13")
        assert isinstance(prereqs, list)

    @pytest.mark.asyncio
    async def test_get_random_kps(self, kb_api):
        """Random KPs are returned."""
        kps = await kb_api.get_random_kps(5)
        assert len(kps) == 5
        assert all(isinstance(k, str) for k in kps)
        # All should be valid KP IDs
        for kp_id in kps:
            kp = await kb_api.get_kp(kp_id)
            assert kp is not None

    @pytest.mark.asyncio
    async def test_get_same_type_kps(self, kb_api):
        """Same-type KPs are retrieved based on related_types."""
        # KP_3_01 likely has related_types
        kps = await kb_api.get_same_type_kps("KP_3_01")
        assert isinstance(kps, list)
        # Should not include the source KP
        kp_ids = [k["kp_id"] for k in kps]
        assert "KP_3_01" not in kp_ids

    @pytest.mark.asyncio
    async def test_get_weak_kps_excludes_mastered(self, kb_api):
        """Weak KPs exclude already mastered ones."""
        mastered = ["KP_1_01", "KP_2_01"]
        weak = await kb_api.get_weak_kps(mastered, count=5)
        assert all(k not in mastered for k in weak)

    @pytest.mark.asyncio
    async def test_get_method(self, kb_api):
        """Methods can be retrieved by name."""
        import json
        with open("data/knowledge_ontology/methods.json", encoding="utf-8") as f:
            methods_data = json.load(f)
        methods_list = methods_data.get("methods", methods_data)
        if methods_list:
            method_name = methods_list[0]["name"]
            method = await kb_api.get_method(method_name)
            assert method is not None
            assert method["name"] == method_name

    @pytest.mark.asyncio
    async def test_get_methods_for_kps(self, kb_api):
        """Methods for given KPs are retrieved."""
        # Get methods for first few KPs
        methods = await kb_api.get_methods_for_kps(["KP_1_01", "KP_2_01"])
        assert isinstance(methods, list)