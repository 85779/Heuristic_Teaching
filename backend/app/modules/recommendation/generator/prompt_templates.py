"""Prompt templates for problem generation.

Builds LLM prompts for generating math problems based on knowledge anchors.
"""

from typing import Optional
from app.modules.recommendation.models import KnowledgeAnchor, KnowledgePoint


class ProblemPromptTemplates:
    """Templates for building problem generation prompts."""

    DIFFICULTY_DESCRIPTIONS = {
        1: "基础计算题（直接套用公式）",
        2: "简单应用题（1-2步推导）",
        3: "标准练习题（多步推导，需要基本技巧）",
        4: "较难题（需要较强技巧或分类讨论）",
        5: "竞赛难度（综合技巧，创新思路）",
    }

    def build_generation_prompt(
        self,
        anchor: KnowledgeAnchor,
        target_difficulty: int = 3,
    ) -> str:
        """Build the full generation prompt for LLM.

        Args:
            anchor: Knowledge anchor containing target KPs and methods.
            target_difficulty: Target difficulty level 1-5.

        Returns:
            Complete prompt string for the LLM.
        """
        kp_context = self._format_kps(anchor.target_kps)

        # Collect valid KP IDs from target KPs
        valid_kp_ids = [kp.kp_id for kp in anchor.target_kps[:5] if kp.kp_id]
        kp_ids_hint = f"\n（有效知识点ID列表：{', '.join(valid_kp_ids)}）" if valid_kp_ids else ""

        method_context = ""
        if anchor.target_method:
            method_context = f"""
## 推荐使用方法
- 方法名：{anchor.target_method.name}
- 方法描述：{anchor.target_method.description}
"""
        elif anchor.target_kps and anchor.target_kps[0].methods:
            first_method = anchor.target_kps[0].methods[0]
            method_context = f"""
## 优先使用方法
- {first_method}
"""

        exclude_context = ""
        if anchor.exclude_similar:
            exclude_context = f"""
## 排除相似题
以下题目已在近期出现，避免生成过于相似的内容：
{chr(10).join(f'- {s}' for s in anchor.exclude_similar[:3])}
"""

        difficulty_desc = self.DIFFICULTY_DESCRIPTIONS.get(
            target_difficulty, f"难度{target_difficulty}"
        )

        prompt = f"""# 高中数学练习题生成任务

## 知识点锚点
{kp_context}

{method_context}
## 目标难度
{difficulty_desc}（1=基础计算，3=标准练习，5=竞赛难度）

## 题目生成要求
1. 围绕上述知识点生成，难度控制在 {target_difficulty} 级
2. 题目条件充分、表述清晰、有唯一答案
3. 使用 LaTeX 格式书写数学表达式（用 $...$ 或 \\(...\\))
4. 生成后自行评估难度并填入 difficulty_rating
5. related_kps 必须从上述有效ID列表中选择，不要编造新ID

{exclude_context}

## 输出格式（严格JSON，不要有其他内容）
{kp_ids_hint}
{{
  "problem_text": "题目内容（LaTeX格式）",
  "answer": "标准答案",
  "solution_hint": "1-2句话解题提示",
  "difficulty_rating": {target_difficulty},
  "related_kps": ["KP_XXX", ...],
  "method_used": "使用方法名",
  "why_recommended": "推荐理由",
  "generation_reasoning": "生成思路（1句话）"
}}

现在开始生成。"""
        return prompt

    def _format_kps(self, kps: list[KnowledgePoint]) -> str:
        """Format knowledge points into readable context.
        
        Args:
            kps: List of KnowledgePoint objects.
            
        Returns:
            Formatted string describing the KPs.
        """
        if not kps:
            return "（未指定具体知识点）"
        
        parts = []
        for i, kp in enumerate(kps[:3], 1):
            part = f"### 知识点 {i}：{kp.name}"
            if kp.content:
                part += f"\n内容：{kp.content}"
            if kp.formula:
                part += f"\n公式：{kp.formula}"
            if kp.related_types:
                part += f"\n相关题型：{', '.join(kp.related_types[:3])}"
            if kp.methods:
                part += f"\n适用方法：{', '.join(kp.methods[:3])}"
            parts.append(part)
        return "\n\n".join(parts)