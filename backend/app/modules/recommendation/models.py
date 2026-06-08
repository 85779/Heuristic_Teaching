"""Data models for the recommendation module."""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field


class TriggerOutcome(str, Enum):
    SOLVED = "SOLVED"
    MAX_ESCALATION = "MAX_ESCALATION"
    ABANDONED = "ABANDONED"
    MANUAL = "MANUAL"


class AnchorType(str, Enum):
    SAME_KP = "SAME_KP"
    VARIATION = "VARIATION"
    BALANCED = "BALANCED"


@dataclass
class RecentProblem:
    problem_id: str = ""
    topic: str = ""
    difficulty: int = 1
    solved_at: Optional[datetime] = None


@dataclass
class KnowledgePoint:
    kp_id: str
    name: str
    chapter: str
    chapter_name: str
    type: str
    content: str = ""
    formula: Optional[str] = None
    related_types: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)


@dataclass
class Method:
    method_id: str = ""
    name: str = ""
    description: str = ""
    examples: list[str] = field(default_factory=list)
    applicable_kps: list[str] = field(default_factory=list)


class TriggerEvent(BaseModel):
    outcome: TriggerOutcome = Field(..., description="触发结果")
    current_problem_kps: List[str] = Field(default_factory=list)
    current_method: Optional[str] = Field(None)
    current_difficulty: int = Field(3, ge=1, le=5)
    session_id: str = Field(..., description="会话ID")
    model_config = ConfigDict(json_schema_extra={"example": {"outcome": "MAX_ESCALATION", "current_problem_kps": ["KP_3_13"], "current_method": None, "current_difficulty": 3, "session_id": "sess_001"}})


class StudentProfile(BaseModel):
    student_id: str = Field(..., description="学生ID")
    dimension_ratio: float = Field(0.5, ge=0.0, le=1.0)
    recent_problems: List[RecentProblem] = Field(default_factory=list)
    weak_kps: List[str] = Field(default_factory=list)
    mastered_kps: List[str] = Field(default_factory=list)
    recent_methods: List[str] = Field(default_factory=list)
    model_config = ConfigDict(json_schema_extra={"example": {"student_id": "student_001", "dimension_ratio": 0.65, "weak_kps": ["KP_3_13"], "mastered_kps": [], "recent_methods": []}})


class KnowledgeAnchor(BaseModel):
    anchor_type: AnchorType = Field(..., description="锚点类型")
    target_kps: List[KnowledgePoint] = Field(default_factory=list)
    target_method: Optional[Method] = Field(None)
    exclude_methods: List[str] = Field(default_factory=list)
    exclude_similar: List[str] = Field(default_factory=list)
    generation_goal: str = Field("", description="生成目标")
    model_config = ConfigDict(json_schema_extra={"example": {"anchor_type": "SAME_KP", "target_kps": [], "generation_goal": "巩固前置知识点"}})


class GeneratedProblem(BaseModel):
    generated_id: str = Field("", description="生成ID")
    problem_text: str = Field("", description="题目文本")
    answer: str = Field("", description="答案")
    solution_hint: str = Field("", description="解题提示")
    difficulty: int = Field(3, ge=1, le=5)
    related_kps: List[str] = Field(default_factory=list)
    method_used: str = Field("", description="使用方法")
    why_recommended: str = Field("", description="推荐理由")
    generation_reasoning: str = Field("", description="生成推理")
    model_config = ConfigDict(json_schema_extra={"example": {"generated_id": "gen_001", "problem_text": "求函数...", "answer": "x=2", "solution_hint": "先求导", "difficulty": 2, "related_kps": ["KP_3_13"], "method_used": "配方法", "why_recommended": "巩固练习", "generation_reasoning": "基于锚点生成"}})


class ValidationResult(BaseModel):
    passed: bool = Field(False)
    errors: List[str] = Field(default_factory=list)


class GenerationResult(BaseModel):
    success: bool = Field(False)
    problem: Optional[GeneratedProblem] = Field(None)
    error: Optional[str] = Field(None)


class RecommendRequest(BaseModel):
    student_id: str = Field(..., description="学生ID")
    trigger: TriggerEvent = Field(..., description="触发事件")
    model_config = ConfigDict(json_schema_extra={"example": {"student_id": "student_001", "trigger": {}}})


class RecommendResponse(BaseModel):
    success: bool = Field(True)
    recommendation: Optional[GeneratedProblem] = Field(None)
    metadata: dict = Field(default_factory=dict)
    error: Optional[dict] = Field(None)
    model_config = ConfigDict(json_schema_extra={"example": {"success": True, "recommendation": None, "metadata": {"generation_time_ms": 1850}, "error": None}})
