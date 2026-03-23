"""Data models for the solving module."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SolvingSession(BaseModel):
    """Model representing a problem-solving session."""

    session_id: str = Field(..., description="Unique session identifier")
    problem_id: str = Field(..., description="ID of the problem being solved")
    status: str = Field(default="started", description="Current session status")
    current_phase: str = Field(default="orientation", description="Current phase")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OrientationResult(BaseModel):
    """Model for orientation phase results."""

    session_id: str = Field(..., description="Session ID")
    understanding: str = Field(..., description="Problem understanding")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts identified")
    goals: List[str] = Field(default_factory=list, description="Learning goals")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class ReconstructionResult(BaseModel):
    """Model for reconstruction phase results."""

    session_id: str = Field(..., description="Session ID")
    components: List[str] = Field(default_factory=list, description="Problem components")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Component relationships")
    breakdown: str = Field(..., description="Problem breakdown")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class TransformationResult(BaseModel):
    """Model for transformation phase results."""

    session_id: str = Field(..., description="Session ID")
    strategies: List[str] = Field(default_factory=list, description="Solution strategies")
    approach: str = Field(..., description="Proposed approach")
    steps: List[str] = Field(default_factory=list, description="Solution steps")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class VerificationResult(BaseModel):
    """Model for verification phase results."""

    session_id: str = Field(..., description="Session ID")
    is_valid: bool = Field(..., description="Whether solution is valid")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    corrections: List[str] = Field(default_factory=list, description="Suggested corrections")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Completion timestamp")


class SolvingEvent(BaseModel):
    """Model for solving-related events."""

    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    session_id: str = Field(..., description="Associated session ID")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


# ============== Input/Output Models ==============

class SolvingRequest(BaseModel):
    """解题请求"""
    problem: str = Field(..., description="LaTeX 题干")
    student_work: Optional[str] = Field(None, description="LaTeX 学生已完成部分")
    model: str = Field(default="qwen-turbo", description="使用的模型")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=8192, description="最大生成长度")
    enable_thinking: bool = Field(default=False, description="启用深度思考（qwen3.5-plus 等）")


class SolvingResponse(BaseModel):
    """解题响应"""
    success: bool = Field(..., description="是否成功")
    evaluation: "EvaluationResult" = Field(..., description="评估结果")
    solution: Optional["ReferenceSolution"] = Field(None, description="完整解法(评估通过时)")
    error_feedback: Optional["ErrorFeedback"] = Field(None, description="错误提示(评估未通过时)")


# ============== Evaluation Models ==============

class DetailLevel(str, Enum):
    """错误提示粒度级别 (预留扩展)"""
    SIMPLE = "simple"  # 仅提示有误
    REASON = "reason"  # 提示原因+方向
    FULL = "full"  # 详细分析


class Issue(BaseModel):
    """问题描述"""
    step: Optional[int] = Field(None, description="涉及的步骤号")
    location: str = Field(..., description="问题位置描述")
    description: str = Field(..., description="问题描述")
    severity: str = Field(default="error", description="error / warning / hint")
    detail_level: DetailLevel = Field(default=DetailLevel.SIMPLE, description="详情粒度级别")


class EvaluationResult(BaseModel):
    """评估结果"""
    is_correct: bool = Field(..., description="学生解答是否正确")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="评估置信度")
    issues: List[Issue] = Field(default_factory=list, description="发现的问题列表")
    can_continue: bool = Field(default=True, description="是否可以继续生成")
    breakpoint_step: Optional[int] = Field(None, description="断点步骤号(可继续时)")


class ErrorFeedback(BaseModel):
    """错误反馈"""
    summary: str = Field(..., description="总体反馈")
    issues: List[Issue] = Field(default_factory=list, description="问题列表")
    suggestion: str = Field(default="", description="修正建议(可选)")


# ============== Reference Solution Models ==============

class Orientation(BaseModel):
    """问题定向"""
    target: str = Field(..., description="目标/已知/所求")
    core_info: List[str] = Field(default_factory=list, description="核心信息")
    difficulty: str = Field(..., description="真正困难点")
    observation: str = Field(..., description="关键观察点")


class Reconstruction(BaseModel):
    """关系重构"""
    missing_link: str = Field(..., description="缺失的联系")
    bridge_strategy: str = Field(..., description="搭桥策略")
    purpose: str = Field(..., description="转化目的")


class Formalization(BaseModel):
    """形式化归"""
    transformations: List[str] = Field(default_factory=list, description="关键变形")
    judgments: List[str] = Field(default_factory=list, description="关键判断")
    classification: str = Field(default="", description="分类讨论")


class Verification(BaseModel):
    """结果审查"""
    conclusion_check: str = Field(..., description="结论检验")
    completeness_check: str = Field(..., description="完整性检验")
    edge_cases: List[str] = Field(default_factory=list, description="边界情形")
    lesson: str = Field(..., description="高层思维动作")


class SolutionStep(BaseModel):
    """解法步骤"""
    order: int = Field(..., description="步骤序号")
    description: str = Field(..., description="步骤描述")
    reasoning: str = Field(..., description="为什么这样做")
    role: str = Field(..., description="在整个解链条中的作用")


class TeachingStep(BaseModel):
    """教学步骤"""
    step_id: str = Field(..., description="步骤ID，如 s1, s2, s3")
    step_name: str = Field(..., description="步骤名称")
    content: str = Field(..., description="步骤内容")


class ProblemAction(BaseModel):
    """解题动作"""
    action_type: str = Field(..., description="动作类型")
    application: str = Field(..., description="具体应用")
    purpose: str = Field(..., description="目的")


class ReferenceSolution(BaseModel):
    """完整参考解法"""
    problem: str = Field(..., description="原始题目(LaTeX)")
    answer: Optional[str] = Field(None, description="答案")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="生成时间")
    
    # 教学步骤
    steps: List[TeachingStep] = Field(default_factory=list, description="教学步骤列表")


# ============== Update forward references ==============
SolvingResponse.model_rebuild()