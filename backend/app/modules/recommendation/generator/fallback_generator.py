"""Fallback generator for when LLM generation fails.

Provides simple hardcoded problems as fallback when LLM is unavailable
or generation consistently fails.
"""

import random
import uuid
from typing import Optional
from app.modules.recommendation.models import GeneratedProblem, KnowledgeAnchor


class FallbackGenerator:
    """Fallback problem generator with curated problem templates.
    
    Used when LLM generation fails to ensure the system always
    returns something usable for demo purposes.
    """

    # Curated fallback problems by chapter/difficulty
    FALLBACK_PROBLEMS = [
        {
            "difficulty": 5,
            "problem_text": "已知 $a, b, c > 0$ 且 $abc = 1$，求证：$\\frac{1}{a^3(b+c)} + \\frac{1}{b^3(c+a)} + \\frac{1}{c^3(a+b)} \\ge \\frac{3}{2}$",
            "answer": "利用 $abc=1$ 将通分后的分母变形，再用均值不等式 $\\frac{x}{y} + \\frac{y}{x} \\ge 2$",
            "solution_hint": "利用条件 $abc=1$ 对称变形，综合运用均值不等式和柯西不等式",
            "method": "不等式综合运用",
            "kps": ["KP_4_05"],
        },
        {
            "difficulty": 5,
            "problem_text": "设 $f(x) = \\ln(1+x) - x + \\frac{x^2}{2}$，讨论 $f(x)$ 在 $(0, +\\infty)$ 上的单调性并证明 $\\ln(1+x) < x - \\frac{x^2}{2} + \\frac{x^3}{3}$ 对一切 $x > 0$ 成立",
            "answer": "$f'(x) = \\frac{x^2}{1+x} > 0$，用泰勒公式展开递推证明",
            "solution_hint": "求导后用泰勒展开逐阶比较余项，利用各阶导数符号递推",
            "method": "导数与泰勒展开",
            "kps": ["KP_3_14"],
        },
        {
            "difficulty": 1,
            "problem_text": "计算：$\\int_0^1 3x^2 dx$",
            "answer": "$1$",
            "solution_hint": "直接使用幂函数的积分公式：$\\int x^n dx = \\frac{x^{n+1}}{n+1}$",
            "method": "定积分计算",
            "kps": ["KP_6_01"],
        },
        {
            "difficulty": 1,
            "problem_text": "计算：$\\lim_{x \\to 0} \\frac{\\sin 3x}{x}$",
            "answer": "3",
            "solution_hint": "利用重要极限 $\\lim_{x \\to 0} \\frac{\\sin x}{x} = 1$",
            "method": "等价无穷小替换",
            "kps": ["KP_3_01"],
        },
        {
            "difficulty": 2,
            "problem_text": "求和：$S_n = 1 + 2 + 4 + \\cdots + 2^{n-1}$",
            "answer": "$2^n - 1$",
            "solution_hint": "这是等比数列求和，使用公式 $S_n = \\frac{a_1(1-q^n)}{1-q}$",
            "method": "等比数列求和",
            "kps": ["KP_1_03"],
        },
        {
            "difficulty": 2,
            "problem_text": "设函数 $f(x) = x^2 - 3x + 2$，求 $f'(x)$",
            "answer": "$2x - 3$",
            "solution_hint": "使用导数的幂法则：$(x^n)' = nx^{n-1}$",
            "method": "求导法则",
            "kps": ["KP_2_01"],
        },
        {
            "difficulty": 3,
            "problem_text": "求不定积分 $\\int x e^x dx$",
            "answer": "$(x-1)e^x + C$",
            "solution_hint": "使用分部积分法：$\\int u dv = uv - \\int v du$",
            "method": "分部积分",
            "kps": ["KP_4_02"],
        },
        {
            "difficulty": 3,
            "problem_text": "判断级数 $\\sum_{n=1}^{\\infty} \\frac{(-1)^{n-1}}{n}$ 的敛散性",
            "answer": "收敛（条件收敛）",
            "solution_hint": "交错级数用莱布尼茨判别法：单调递减趋于0则收敛",
            "method": "级数审敛法",
            "kps": ["KP_5_03"],
        },
        {
            "difficulty": 1,
            "problem_text": "解方程：$2x + 5 = 13$",
            "answer": "$x = 4$",
            "solution_hint": "移项得 $2x = 8$，两边除以2",
            "method": "一元一次方程",
            "kps": ["KP_1_01"],
        },
        {
            "difficulty": 2,
            "problem_text": "化简：$\\frac{x^2 - 4}{x - 2}$",
            "answer": "$x + 2$（$x \\neq 2$）",
            "solution_hint": "分子分解因式：$x^2 - 4 = (x-2)(x+2)$",
            "method": "因式分解",
            "kps": ["KP_1_02"],
        },
        {
            "difficulty": 4,
            "problem_text": "设 $a_n = \\frac{2n}{n+1}$，求 $\\lim_{n \\to \\infty} a_n$ 并证明",
            "answer": "$\\lim_{n \\to \\infty} a_n = 2$",
            "solution_hint": "分子分母同除以n：$a_n = \\frac{2}{1 + 1/n}$，当 $n \\to \\infty$ 时 $1/n \\to 0$",
            "method": "数列极限证明",
            "kps": ["KP_3_02"],
        },
        # === Expanded coverage ===
        {
            "difficulty": 3,
            "problem_text": "已知复数 $z = 1 + \\sqrt{3}i$，求 $|z|$ 和 $\\arg(z)$",
            "answer": "$|z| = 2$，$\\arg(z) = \\frac{\\pi}{3}$",
            "solution_hint": "模长 $|z| = \\sqrt{a^2 + b^2}$，辐角 $\\arg(z) = \\arctan(b/a)$",
            "method": "复数运算",
            "kps": ["KP_7_01"],
        },
        {
            "difficulty": 4,
            "problem_text": "已知椭圆 $\\frac{x^2}{a^2} + \\frac{y^2}{b^2} = 1$ 的离心率为 $\\frac{\\sqrt{3}}{2}$，且过点 $(2, 1)$，求椭圆方程",
            "answer": "$\\frac{x^2}{8} + \\frac{y^2}{2} = 1$",
            "solution_hint": "由 $e = c/a$ 和 $a^2 = b^2 + c^2$ 建立方程，代入点坐标求解",
            "method": "椭圆方程求解",
            "kps": ["KP_8_05"],
        },
        {
            "difficulty": 3,
            "problem_text": "在正方体 $ABCD-A_1B_1C_1D_1$ 中，求异面直线 $BD_1$ 与 $AC$ 所成角的余弦值",
            "answer": "$\\frac{\\sqrt{6}}{6}$",
            "solution_hint": "建立空间直角坐标系，用向量法求异面直线夹角",
            "method": "空间向量法",
            "kps": ["KP_9_05"],
        },
        {
            "difficulty": 3,
            "problem_text": "从 5 名男生和 4 名女生中选出 4 人参加比赛，要求至少有 2 名女生，有多少种选法？",
            "answer": "81 种",
            "solution_hint": "分类讨论：2女2男 + 3女1男 + 4女，分别计算组合数求和",
            "method": "分类计数原理",
            "kps": ["KP_10_01"],
        },
        {
            "difficulty": 2,
            "problem_text": "已知 $\\sin\\alpha = \\frac{3}{5}$，$\\alpha \\in (\\frac{\\pi}{2}, \\pi)$，求 $\\cos\\alpha$ 和 $\\tan\\alpha$",
            "answer": "$\\cos\\alpha = -\\frac{4}{5}$，$\\tan\\alpha = -\\frac{3}{4}$",
            "solution_hint": "用同角三角函数关系 $\\sin^2\\alpha + \\cos^2\\alpha = 1$，注意象限确定符号",
            "method": "同角三角函数关系",
            "kps": ["KP_4_01"],
        },
        {
            "difficulty": 2,
            "problem_text": "同时抛掷两枚均匀硬币，求恰好一枚正面朝上的概率",
            "answer": "$\\frac{1}{2}$",
            "solution_hint": "样本空间：{正正, 正反, 反正, 反反}，4个等可能结果",
            "method": "古典概型",
            "kps": ["KP_12_01"],
        },
        {
            "difficulty": 5,
            "problem_text": "已知函数 $f(x) = \\ln x - ax + \\frac{1-a}{x} - 1$，讨论 $f(x)$ 的单调性，并证明当 $a \\le \\frac{1}{2}$ 时 $f(x) \\le 0$",
            "answer": "$a \\le 0$ 时递增；$0 < a < 1$ 时先减后增；$a \\ge 1$ 时递减",
            "solution_hint": "求导后分子是二次函数，分类讨论判别式符号确定导数零点分布",
            "method": "含参导数综合",
            "kps": ["KP_3_17", "KP_3_18"],
        },
        {
            "difficulty": 4,
            "problem_text": "用数学归纳法证明：$1 \\cdot 2 + 2 \\cdot 3 + \\cdots + n(n+1) = \\frac{n(n+1)(n+2)}{3}$",
            "answer": "归纳奠基 $n=1$ 成立，归纳递推利用假设代入化简",
            "solution_hint": "设 $n=k$ 时成立，证明 $n=k+1$ 时 $S_{k+1} = S_k + (k+1)(k+2)$",
            "method": "数学归纳法",
            "kps": ["KP_11_03"],
        },
    ]

    async def generate(
        self,
        anchor: KnowledgeAnchor,
        target_difficulty: int = 3,
        reason: str = "",
    ) -> GeneratedProblem:
        """Generate a fallback problem.
        
        Args:
            anchor: Knowledge anchor (used for context, not generation).
            target_difficulty: Desired difficulty 1-5.
            reason: Why fallback was triggered.
            
        Returns:
            A GeneratedProblem from curated templates.
        """
        # Filter by difficulty
        candidates = [p for p in self.FALLBACK_PROBLEMS 
                     if abs(p["difficulty"] - target_difficulty) <= 1]
        if not candidates:
            candidates = self.FALLBACK_PROBLEMS

        template = random.choice(candidates)

        return GeneratedProblem(
            generated_id=f"fallback_{uuid.uuid4().hex[:8]}",
            problem_text=template["problem_text"],
            answer=template["answer"],
            solution_hint=template["solution_hint"],
            difficulty=template["difficulty"],
            related_kps=template["kps"],
            method_used=template["method"],
            why_recommended=anchor.generation_goal or "根据知识锚点推荐",
            generation_reasoning=f"后备生成器：{reason}" if reason else "后备生成器生成",
        )