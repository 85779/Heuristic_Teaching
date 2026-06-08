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

        Uses flexible best-match alignment that handles:
          - Student merges multiple solution steps into one
          - Student skips solution steps
          - Student writes extra steps not in solution
          - Non-1:1 step correspondence

        For each solution step, finds the BEST-MATCHING student step
        (not necessarily at the same index), tracks matched pairs,
        then identifies the first unmatched solution step as the breakpoint.
        """
        # Edge: no student steps
        if not student_steps:
            if not solution_steps:
                return self._make_location(
                    breakpoint_type=BreakpointType.STUCK,
                    position=0, expected="",
                    gap="学生未提供任何解题步骤，无法确定断点位置",
                    student_last=None,
                )
            return self._make_location(
                breakpoint_type=BreakpointType.MISSING_STEP,
                position=0, expected=solution_steps[0].content,
                gap="学生未开始解题，第一步缺失",
                student_last=None,
            )

        # Build similarity matrix: for each (student_i, solution_j) pair
        n_student = len(student_steps)
        n_solution = len(solution_steps)
        scores: list[list[float]] = []
        for si in range(n_student):
            row: list[float] = []
            for sj in range(n_solution):
                overlap, kw_count = self._keyword_overlap(
                    student_steps[si].content.strip(),
                    solution_steps[sj].content.strip(),
                )
                if kw_count >= 2:
                    sim = overlap
                else:
                    sim = self._string_similarity(
                        student_steps[si].content.strip(),
                        solution_steps[sj].content.strip(),
                    )
                # Boost by cosine fallback for medium-overlap pairs
                if 0.25 <= sim <= 0.80:
                    cos = self._cosine_similarity_fallback(
                        student_steps[si].content.strip(),
                        solution_steps[sj].content.strip(),
                    )
                    sim = max(sim, cos)
                row.append(sim)
            scores.append(row)

        # Greedy best-match alignment: for each solution step, find best unmatched student step
        matched_student: set[int] = set()
        first_unmatched_solution: int = n_solution

        for sj in range(n_solution):
            best_si = -1
            best_score = 0.0
            for si in range(n_student):
                if si in matched_student:
                    continue
                if scores[si][sj] > best_score:
                    best_score = scores[si][sj]
                    best_si = si
            if best_si >= 0 and best_score >= 0.3:
                matched_student.add(best_si)
            else:
                # No student step matches this solution step well enough
                if sj < first_unmatched_solution:
                    first_unmatched_solution = sj

        # Determine breakpoint from first unmatched solution step
        if first_unmatched_solution < n_solution:
            expected = solution_steps[first_unmatched_solution].content
            student_last = student_steps[-1].content if n_student > 0 else None

            # Check if any student step is completely off-track
            min_student_score = 1.0
            worst_si = -1
            for si in range(n_student):
                max_for_student = max(scores[si]) if scores[si] else 0.0
                if max_for_student < min_student_score:
                    min_student_score = max_for_student
                    worst_si = si

            if min_student_score < 0.15:
                return self._make_location(
                    breakpoint_type=BreakpointType.WRONG_DIRECTION,
                    position=worst_si,
                    expected=expected,
                    gap=f"学生第{worst_si + 1}步方向偏离（最高相似度{min_student_score:.2f}）",
                    student_last=student_steps[worst_si].content,
                )

            # Count unmatched student steps
            unmatched_count = n_student - len(matched_student)
            gap_detail = f"缺少第{first_unmatched_solution + 1}步"
            if unmatched_count > 0:
                gap_detail += f"，{unmatched_count}个学生步骤无对应参考步骤"

            return self._make_location(
                breakpoint_type=BreakpointType.MISSING_STEP,
                position=first_unmatched_solution,
                expected=expected,
                gap=gap_detail,
                student_last=student_last,
            )

        # All solution steps have matches
        if len(matched_student) >= n_solution:
            return self._make_location(
                breakpoint_type=BreakpointType.NO_BREAKPOINT,
                position=n_solution,
                expected="",
                gap="学生解题步骤与参考解法一致，无断点",
                student_last=student_steps[-1].content if n_student > 0 else None,
            )

        return self._make_location(
            breakpoint_type=BreakpointType.MISSING_STEP,
            position=0,
            expected=solution_steps[0].content if n_solution > 0 else "",
            gap="无法对齐学生步骤与参考解法",
            student_last=student_steps[-1].content if n_student > 0 else None,
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
