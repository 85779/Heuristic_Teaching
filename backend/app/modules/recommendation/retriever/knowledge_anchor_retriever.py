"""Knowledge Anchor Retriever for recommendation system.

Retrieves appropriate knowledge anchors based on student dimension profile
and current learning context.
"""

from typing import Optional
from app.modules.recommendation.models import (
    AnchorType,
    KnowledgeAnchor,
    StudentProfile,
    KnowledgePoint,
    Method,
)
from app.modules.recommendation.knowledge_base.knowledge_api import KnowledgeBaseAPI


class KnowledgeAnchorRetriever:
    """Retriever for knowledge anchors based on student profile.

    Decides anchor strategy based on dimension_ratio:
    - R-type (ratio > 0.65): SAME_KP anchor - reinforce prerequisites
    - M-type (ratio < 0.35): VARIATION anchor - same type, different method
    - Balanced (0.35 <= ratio <= 0.65): BALANCED anchor - random weak KPs
    """

    def __init__(self, kb_api: KnowledgeBaseAPI):
        """Initialize the retriever.

        Args:
            kb_api: KnowledgeBaseAPI instance for querying knowledge base.
        """
        self._kb = kb_api

    async def retrieve(
        self,
        profile: StudentProfile,
        current_kps: list[str],
        current_method: Optional[str]
    ) -> KnowledgeAnchor:
        """Retrieve appropriate knowledge anchor based on student profile.

        Args:
            profile: Student profile with dimension_ratio, mastered_kps, weak_kps, etc.
            current_kps: KP IDs of the current problem.
            current_method: Method used in current problem (if any).

        Returns:
            KnowledgeAnchor with target KPs, methods, and generation goal.
        """
        ratio = profile.dimension_ratio

        if ratio > 0.65:
            # R型薄弱 → 同KP + 前置KP补强
            return await self._anchor_same_kp(profile, current_kps)
        elif ratio < 0.35:
            # M型薄弱 → 同题型不同方法变式
            return await self._anchor_variation(profile, current_kps, current_method)
        else:
            # 均衡 → 随机薄弱KP
            return await self._anchor_balanced(profile)

    async def _anchor_same_kp(
        self,
        profile: StudentProfile,
        current_kps: list[str]
    ) -> KnowledgeAnchor:
        """Get SAME_KP anchor: reinforce prerequisite knowledge.

        Strategy: Find prerequisite KPs that are not yet mastered,
        and use those as target for generation.
        """
        # 1. Collect all prerequisites from current KPs
        prereq_ids = set()
        for kp_id in current_kps:
            prereqs = await self._kb.get_prerequisites(kp_id)
            prereq_ids.update(prereqs)

        # 2. Filter out already mastered
        weak_prereqs = [k for k in prereq_ids if k not in profile.mastered_kps]

        # 3. Limit to 3 and use as anchor
        target_kp_ids = (list(weak_prereqs) or current_kps)[:3]
        target_kps_data = await self._kb.get_kps(target_kp_ids)

        # Convert to KnowledgePoint dataclass
        target_kps = []
        for kp_dict in target_kps_data:
            target_kps.append(KnowledgePoint(
                kp_id=kp_dict["kp_id"],
                name=kp_dict["name"],
                chapter=kp_dict.get("chapter", ""),
                chapter_name=kp_dict.get("chapter_name", ""),
                type=kp_dict.get("type", ""),
                content=kp_dict.get("content", ""),
                formula=kp_dict.get("formula"),
                related_types=kp_dict.get("related_types", []),
                prerequisites=kp_dict.get("prerequisites", []),
                methods=kp_dict.get("methods", []),
            ))

        return KnowledgeAnchor(
            anchor_type=AnchorType.SAME_KP,
            target_kps=target_kps,
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="巩固前置知识点，强化基础",
        )

    async def _anchor_variation(
        self,
        profile: StudentProfile,
        current_kps: list[str],
        current_method: Optional[str]
    ) -> KnowledgeAnchor:
        """Get VARIATION anchor: same type, different method.

        Strategy: Find KPs of the same type but using different methods
        from what the student recently used.
        """
        if not current_kps:
            return await self._anchor_balanced(profile)

        # Build exclude list: current method + recent methods
        exclude_methods = list(profile.recent_methods)
        if current_method and current_method not in exclude_methods:
            exclude_methods.append(current_method)

        # Get same-type KPs excluding recent methods
        same_type_kps = await self._kb.get_same_type_kps(
            current_kps[0],
            exclude_methods=exclude_methods
        )

        if same_type_kps:
            target_kp_data = same_type_kps[0]
            target_kps = [KnowledgePoint(
                kp_id=target_kp_data["kp_id"],
                name=target_kp_data["name"],
                chapter=target_kp_data.get("chapter", ""),
                chapter_name=target_kp_data.get("chapter_name", ""),
                type=target_kp_data.get("type", ""),
                content=target_kp_data.get("content", ""),
                formula=target_kp_data.get("formula"),
                related_types=target_kp_data.get("related_types", []),
                prerequisites=target_kp_data.get("prerequisites", []),
                methods=target_kp_data.get("methods", []),
            )]

            # Find a method to recommend (prefer one not in exclude list)
            method_name = ""
            for m in target_kp_data.get("methods", []):
                if m not in exclude_methods:
                    method_name = m
                    break
            method_name = method_name or (target_kp_data.get("methods", []) or [""])[0]

            target_method = None
            if method_name:
                method_data = await self._kb.get_method(method_name)
                if method_data:
                    target_method = Method(
                        name=method_data["name"],
                        description=method_data.get("description", ""),
                        applicable_kps=method_data.get("applicable_kps", []),
                    )

            return KnowledgeAnchor(
                anchor_type=AnchorType.VARIATION,
                target_kps=target_kps,
                target_method=target_method,
                exclude_methods=exclude_methods,
                exclude_similar=[],
                generation_goal=f"使用新方法（{method_name}）的变式练习",
            )

        # Fallback to balanced if no variation found
        return await self._anchor_balanced(profile)

    async def _anchor_balanced(self, profile: StudentProfile) -> KnowledgeAnchor:
        """Get BALANCED anchor: random weak KPs for mixed practice.

        Strategy: Use weak KPs if available, otherwise random KPs.
        """
        if profile.weak_kps:
            kp_ids = profile.weak_kps[:2]
        else:
            kp_ids = await self._kb.get_random_kps(2)

        target_kps_data = await self._kb.get_kps(kp_ids)

        target_kps = []
        for kp_dict in target_kps_data:
            target_kps.append(KnowledgePoint(
                kp_id=kp_dict["kp_id"],
                name=kp_dict["name"],
                chapter=kp_dict.get("chapter", ""),
                chapter_name=kp_dict.get("chapter_name", ""),
                type=kp_dict.get("type", ""),
                content=kp_dict.get("content", ""),
                formula=kp_dict.get("formula"),
                related_types=kp_dict.get("related_types", []),
                prerequisites=kp_dict.get("prerequisites", []),
                methods=kp_dict.get("methods", []),
            ))

        return KnowledgeAnchor(
            anchor_type=AnchorType.BALANCED,
            target_kps=target_kps,
            target_method=None,
            exclude_methods=[],
            exclude_similar=[],
            generation_goal="薄弱知识点巩固练习",
        )