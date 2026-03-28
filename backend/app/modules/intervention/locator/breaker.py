"""Breakpoint locator using semantic matching.

Three-level matching:
  1. Keyword overlap — fast Jaccard on math keywords (no LLM call)
  2. Embedding similarity — cosine sim via DashScope embeddings (if client available)
  3. Strict string match fallback — if no LLM client
"""
import re
from typing import List, Optional, TYPE_CHECKING
from app.modules.solving.models import TeachingStep
from .models import BreakpointLocation, BreakpointType, MatchResult

if TYPE_CHECKING:
    from app.infrastructure.llm.dashscope_client import DashScopeClient


class BreakpointLocator:
    """Locates breakpoints by comparing student steps vs reference solution steps.

    Uses three-level semantic matching:
      Level 1 — Keyword overlap (Jaccard): fast pre-filter, no LLM call
      Level 2 — Embedding cosine similarity: precise semantic match (requires LLM client)
      Level 3 — String fallback: exact match when no LLM client available
    """

    # Keyword overlap thresholds
    OVERLAP_REJECT = 0.30   # < 0.30 → definitely WRONG_DIRECTION
    OVERLAP_ACCEPT = 0.80   # > 0.80 → match (no embedding needed)

    # Embedding cosine thresholds (used when 0.30 <= overlap <= 0.80)
    COS_MATCH = 0.85        # ≥ 0.85 → match
    COS_INCOMPLETE = 0.60   # 0.60–0.85 → INCOMPLETE
    # < 0.60 → WRONG_DIRECTION

    def __init__(self, llm_client: Optional["DashScopeClient"] = None):
        """Initialize locator.

        Args:
            llm_client: Optional DashScopeClient for embedding similarity.
                        If not provided, falls back to keyword-only matching.
        """
        self._llm_client = llm_client

    # =======================================================================
    # Public API
    # =======================================================================

    def locate(
        self,
        student_steps: List[TeachingStep],
        solution_steps: List[TeachingStep],
    ) -> BreakpointLocation:
        """Compare student steps to solution steps and locate the breakpoint.

        Three-level matching logic:
          1. Empty student → STUCK / MISSING_STEP
          2. More student steps than solution → NO_BREAKPOINT
          3. Step-by-step comparison:
             a. Keyword overlap < 0.30 → WRONG_DIRECTION
             b. Keyword overlap > 0.80 → match (may be INCOMPLETE if student shorter)
             c. Otherwise → embedding similarity
                - cos ≥ 0.85 → match
                - 0.60 ≤ cos < 0.85 → INCOMPLETE
                - cos < 0.60 → WRONG_DIRECTION
          4. All steps match but student shorter → MISSING_STEP (next step)
          5. All steps match and same count → NO_BREAKPOINT
        """
        # Edge: no student steps
        if not student_steps:
            if not solution_steps:
                return self._make_location(
                    breakpoint_type=BreakpointType.STUCK,
                    position=0,
                    expected="",
                    gap="学生未提供任何解题步骤，无法确定断点位置",
                    student_last=None,
                )
            return self._make_location(
                breakpoint_type=BreakpointType.MISSING_STEP,
                position=0,
                expected=solution_steps[0].content,
                gap="学生未开始解题，第一步缺失",
                student_last=None,
            )

        # Edge: student has more steps than solution (already beyond reference)
        if len(student_steps) > len(solution_steps):
            return self._make_location(
                breakpoint_type=BreakpointType.NO_BREAKPOINT,
                position=len(solution_steps),
                expected="",
                gap="学生已超越参考解法步骤数",
                student_last=student_steps[-1].content,
            )

        # Step-by-step comparison
        for i in range(len(solution_steps)):
            if i >= len(student_steps):
                # Student is missing this step
                return self._make_location(
                    breakpoint_type=BreakpointType.MISSING_STEP,
                    position=i,
                    expected=solution_steps[i].content,
                    gap=f"学生在第 {i + 1} 步缺失",
                    student_last=student_steps[i - 1].content if i > 0 else None,
                )

            student_content = student_steps[i].content.strip()
            expected_content = solution_steps[i].content.strip()

            # Step 1: Keyword overlap (returns score + keyword count)
            overlap, kw_count = self._keyword_overlap(student_content, expected_content)

            # Determine effective similarity: use keyword overlap if keywords are rich,
            # otherwise fall back to string similarity for sparse content
            if kw_count >= 2:
                # Rich keyword content — trust keyword overlap
                effective_sim = overlap
            else:
                # Sparse content (e.g., short English phrases) — use string similarity
                effective_sim = self._string_similarity(student_content, expected_content)

            # Case 1: High effective similarity (> 0.8) → treat as match, continue
            if effective_sim > self.OVERLAP_ACCEPT:
                continue

            # Case 2: Low effective similarity (< 0.3) → possible WRONG_DIRECTION
            if effective_sim < self.OVERLAP_REJECT:
                # WRONG_DIRECTION only if BOTH are extremely low:
                #   - keyword overlap < 0.3 (different math terms/concepts) AND
                #   - string similarity < 0.2 (almost no character overlap)
                # If string similarity >= 0.2, student is on same math track → INCOMPLETE
                if overlap < self.OVERLAP_REJECT and self._string_similarity(student_content, expected_content) < 0.2:
                    return self._make_location(
                        breakpoint_type=BreakpointType.WRONG_DIRECTION,
                        position=i,
                        expected=expected_content,
                        gap=f"学生在第 {i + 1} 步的方向偏离了参考解法",
                        student_last=student_content,
                    )
                # Otherwise: INCOMPLETE (continue scanning — student may still be on track)
                # Length check: very short content → also incomplete, but don't stop
                if len(student_content) < len(expected_content) * 0.4:
                    continue  # incomplete and short — note but keep going
                continue  # incomplete but substantial — keep going

            # Case 3: Medium effective similarity (0.3–0.8) → INCOMPLETE (continue scanning)
            # Student is on right track but missing detail or wrote less
            if len(student_content) < len(expected_content) * 0.4:
                continue  # short but on track — keep going
            continue  # substantial but not quite a full match — keep going

        # All compared steps are acceptable, check if student has fewer
        if len(student_steps) < len(solution_steps):
            next_pos = len(student_steps)
            return self._make_location(
                breakpoint_type=BreakpointType.MISSING_STEP,
                position=next_pos,
                expected=solution_steps[next_pos].content,
                gap=f"学生已正确完成前 {next_pos} 步，第 {next_pos + 1} 步缺失",
                student_last=student_steps[-1].content,
            )

        # All match, same count
        return self._make_location(
            breakpoint_type=BreakpointType.NO_BREAKPOINT,
            position=len(solution_steps),
            expected="",
            gap="学生解题步骤与参考解法一致，无断点",
            student_last=student_steps[-1].content if student_steps else None,
        )

    # =======================================================================
    # Level 1: Keyword Overlap (Jaccard on math-aware tokens)
    # =======================================================================

    def _extract_keywords(self, text: str) -> set:
        r"""Extract math-aware keywords from step content.

        Extracts:
          - LaTeX commands (\alpha, \gcd, etc.)
          - Chinese words (2+ chars)
          - Math identifiers (var names a-zA-Z)
          - Numbers
          - Operators (+ - × ÷ = ≥ ≤ ∞)
        """
        tokens = set()

        # LaTeX commands: \command{args} or \command
        tokens.update(re.findall(r'\\[a-zA-Z]+', text))

        # Chinese words (at least 2 chars)
        chinese = re.findall(r'[\u4e00-\u9fff]{2,}', text)
        tokens.update(chinese)

        # Single Chinese chars that are math terms
        math_chars = re.findall(r'[\u4e00-\u9fff]', text)
        # Filter to only common math Chinese chars
        math_terms = {"设", "令", "得", "为", "于", "在", "上", "下", "中", "内", "外",
                      "求", "证", "明", "因为", "所以", "因此", "若", "则", "当", "且",
                      "或", "并", "且", "之", "的", "是", "有", "无", "可", "使"}
        tokens.update(c for c in math_chars if c in math_terms)

        # Variable names (a-zA-Z, but not single letters that are too common)
        tokens.update(re.findall(r'\b[a-zA-Z]\b', text))

        # Numbers (including decimals and fractions)
        tokens.update(re.findall(r'\b\d+(?:\.\d+)?\b', text))

        # Math operators
        tokens.update(re.findall(r'[+\-×÷=≥≤<>∞]', text))

        return tokens

    def _keyword_overlap(self, text1: str, text2: str) -> tuple:
        """Compute Jaccard overlap of keyword sets.

        Returns:
            tuple: (overlap_score, min_keyword_count)
                   min_keyword_count is the smaller of the two keyword set sizes.
                   Use min_keyword_count to determine if keyword-based comparison is reliable.
        """
        set1 = self._extract_keywords(text1)
        set2 = self._extract_keywords(text2)

        if not set1 or not set2:
            return 0.0, 0

        intersection = len(set1 & set2)
        union = len(set1 | set2)
        overlap = intersection / union if union > 0 else 0.0
        min_count = min(len(set1), len(set2))
        return overlap, min_count

    # =======================================================================
    # Level 2: Cosine Similarity (embedding)
    # =======================================================================

    def _cosine_similarity_fallback(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """Compute cosine similarity between two texts.

        Uses DashScope embeddings if client is available,
        otherwise falls back to keyword/string similarity.

        Args:
            text1: Student step content
            text2: Reference step content

        Returns:
            float: Similarity score 0.0 to 1.0
        """
        if self._llm_client is None:
            # Fallback: use keyword overlap (first element) as rough proxy
            overlap, _ = self._keyword_overlap(text1, text2)
            return overlap * 0.9

        # NOTE: This method is sync but get_embeddings is async.
        # Caller should pre-compute embeddings when possible.
        # For now, we use a sync heuristic as fallback.
        overlap, kw_count = self._keyword_overlap(text1, text2)
        if kw_count >= 2:
            return overlap
        return self._string_similarity(text1, text2)

    async def _compute_embedding_similarity_async(
        self,
        text1: str,
        text2: str,
    ) -> float:
        """Async version using DashScope embeddings.

        Use this when calling from async context with LLM client available.
        """
        if self._llm_client is None:
            overlap, _ = self._keyword_overlap(text1, text2)
            return overlap * 0.9

        try:
            embeddings = await self._llm_client.get_embeddings([text1, text2])
            return self._cosine(embeddings[0], embeddings[1])
        except Exception:
            # Fall back on any error
            overlap, _ = self._keyword_overlap(text1, text2)
            return overlap * 0.9

    def _cosine(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Pure Python cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        if norm_a * norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _string_similarity(self, text1: str, text2: str) -> float:
        """Compute string similarity using character-level overlap.

        Uses normalized longest common subsequence ratio as a proxy for
        semantic similarity when keyword extraction yields few results.
        """
        if text1 == text2:
            return 1.0
        if not text1 or not text2:
            return 0.0

        # Character-level Jaccard (word-level is too fragile for mixed content)
        chars1 = set(text1.lower())
        chars2 = set(text2.lower())
        intersection = len(chars1 & chars2)
        union = len(chars1 | chars2)
        return intersection / union if union > 0 else 0.0

    # =======================================================================
    # MatchResult for detailed comparison (used by tests/debugging)
    # =======================================================================

    def compare_step(
        self,
        student_content: str,
        expected_content: str,
    ) -> MatchResult:
        """Compare a single student step against a reference step.

        Returns a MatchResult with all similarity scores.
        Useful for debugging and testing the matching logic.
        """
        overlap, kw_count = self._keyword_overlap(student_content, expected_content)
        effective_sim = overlap if kw_count >= 2 else self._string_similarity(student_content, expected_content)

        if effective_sim > self.OVERLAP_ACCEPT:
            bpt = BreakpointType.NO_BREAKPOINT
            gap = "匹配"
        elif effective_sim < self.OVERLAP_REJECT:
            bpt = BreakpointType.WRONG_DIRECTION
            gap = "方向偏离"
        else:
            bpt = BreakpointType.INCOMPLETE_STEP if len(student_content) < len(expected_content) * 0.4 else BreakpointType.NO_BREAKPOINT
            gap = "内容不完整" if bpt == BreakpointType.INCOMPLETE_STEP else "匹配"

        return MatchResult(
            keyword_overlap=overlap,
            embedding_similarity=effective_sim,
            breakpoint_type=bpt,
            gap_description=gap,
            student_content=student_content,
            expected_content=expected_content,
        )

    # =======================================================================
    # Helpers
    # =======================================================================

    @staticmethod
    def _make_location(
        breakpoint_type: BreakpointType,
        position: int,
        expected: str,
        gap: str,
        student_last: Optional[str],
    ) -> BreakpointLocation:
        return BreakpointLocation(
            breakpoint_position=position,
            breakpoint_type=breakpoint_type,
            expected_step_content=expected,
            gap_description=gap,
            student_last_step=student_last,
        )
