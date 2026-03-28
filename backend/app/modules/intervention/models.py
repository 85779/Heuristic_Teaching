"""Data models for the intervention module."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field


# ============================================================
# Enums
# ============================================================

class InterventionType(str, Enum):
    """Types of interventions available."""

    HINT = "hint"
    EXPLANATION = "explanation"
    REDIRECT = "redirect"
    EXAMPLE = "example"
    SCAFFOLD = "scaffold"


class InterventionStatus(str, Enum):
    """Status of an intervention."""

    SUGGESTED = "suggested"
    DELIVERED = "delivered"
    ACCEPTED = "accepted"
    DISMISSED = "dismissed"
    IGNORED = "ignored"
    ACTIVE = "active"         # 干预进行中
    COMPLETED = "completed"  # 学生主动结束
    TERMINATED = "terminated"  # AI干预达到极限


class BreakpointTypeEnum(str, Enum):
    """断点类型"""
    MISSING_STEP = "MISSING_STEP"
    WRONG_DIRECTION = "WRONG_DIRECTION"
    INCOMPLETE_STEP = "INCOMPLETE_STEP"
    STUCK = "STUCK"
    NO_BREAKPOINT = "NO_BREAKPOINT"


class DimensionEnum(str, Enum):
    """困难维度"""
    RESOURCE = "Resource"      # 资源侧
    METACOGNITIVE = "Metacognitive"  # 元认知侧


class PromptLevelEnum(str, Enum):
    """提示等级"""
    # Resource 侧
    R1 = "R1"
    R2 = "R2"
    R3 = "R3"
    R4 = "R4"
    # Metacognitive 侧
    M1 = "M1"
    M2 = "M2"
    M3 = "M3"
    M4 = "M4"
    M5 = "M5"


class EscalationAction(str, Enum):
    """升级决策"""
    MAINTAIN = "maintain"                    # 维持当前等级
    ESCALATE = "escalate"                   # 升级
    SWITCH_TO_RESOURCE = "switch_to_resource"  # 切换到Resource维度
    MAX_LEVEL_REACHED = "max_level_reached"  # 达到最高级


class StudentResponseEnum(str, Enum):
    """学生反馈"""
    ACCEPTED = "accepted"            # 学生推进了
    NOT_PROGRESSED = "not_progressed"  # 学生没推进


class FrontendSignalEnum(str, Enum):
    """前端信号"""
    END = "END"          # 直接结束
    ESCALATE = "ESCALATE"  # 强制升级


# ============================================================
# Core Data Classes
# ============================================================

@dataclass
class QaHistory:
    """问答历史"""
    student_q: str  # 学生的问题/行为
    system_a: str    # 系统的提示内容


@dataclass
class EscalationDecision:
    """升级决策"""
    action: EscalationAction
    from_level: str
    to_level: Optional[str] = None
    reasoning: str = ""
    system_response: Optional[str] = None


@dataclass
class DimensionResult:
    """Node 2a 输出"""
    dimension: DimensionEnum
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class SubTypeResult:
    """Node 2b 输出"""
    sub_type: PromptLevelEnum
    confidence: float = 0.0
    reasoning: str = ""
    hint_direction: str = ""
    escalation_decision: Optional[EscalationDecision] = None


@dataclass
class BreakpointLocation:
    """断点位置（Node 1 输出）"""
    breakpoint_position: int
    breakpoint_type: BreakpointTypeEnum
    expected_step_content: str
    gap_description: str
    student_last_step: Optional[str] = None


@dataclass
class InterventionRecord:
    """干预记录"""
    turn: int
    qa_history: QaHistory
    prompt_level: str
    prompt_content: str
    student_response: StudentResponseEnum
    frontend_signal: Optional[FrontendSignalEnum] = None
    breakpoint_status: str = "persistent"  # "resolved" | "persistent"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class InterventionContext:
    """Node间传递的上下文"""
    session_id: str
    student_id: str
    problem_context: str
    student_input: str
    solution_steps: List[Dict[str, Any]]
    student_steps: List[Dict[str, Any]]
    breakpoint_location: Optional[BreakpointLocation] = None
    dimension_result: Optional[DimensionResult] = None
    sub_type_result: Optional[SubTypeResult] = None
    intervention_memory: List[InterventionRecord] = field(default_factory=list)
    current_level: str = ""
    status: InterventionStatus = InterventionStatus.ACTIVE

    def is_active(self) -> bool:
        return self.status == InterventionStatus.ACTIVE

    def is_terminated(self) -> bool:
        return self.status == InterventionStatus.TERMINATED

    def is_completed(self) -> bool:
        return self.status == InterventionStatus.COMPLETED


# ============================================================
# Pydantic Models (for API)
# ============================================================

class Intervention(BaseModel):
    """Intervention model representing a learning intervention."""

    id: str = Field(..., description="Unique intervention identifier")
    student_id: str = Field(..., description="Student identifier")
    session_id: str = Field(..., description="Session identifier")
    intervention_type: InterventionType = Field(..., description="Type of intervention")
    status: InterventionStatus = Field(default=InterventionStatus.SUGGESTED, description="Intervention status")
    content: str = Field(..., description="Intervention content text")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0, description="Intensity level (0.0-1.0)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    delivered_at: Optional[datetime] = Field(default=None, description="Delivery timestamp")
    outcome_at: Optional[datetime] = Field(default=None, description="Outcome timestamp")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "id": "int_12345",
                "student_id": "student_001",
                "session_id": "session_001",
                "intervention_type": "hint",
                "status": "suggested",
                "content": "Consider breaking down the problem into smaller steps.",
                "intensity": 0.3,
                "metadata": {"reason": "student_stuck", "location": "step_3"},
            }
        }


class InterventionRequest(BaseModel):
    """Request model for creating an intervention."""

    student_id: str = Field(..., description="Student identifier")
    session_id: str = Field(..., description="Session identifier")
    student_input: str = Field(default="", description="学生当前输入")
    frontend_signal: Optional[FrontendSignalEnum] = Field(None, description="前端信号: END / ESCALATE")
    intervention_type: Optional[InterventionType] = Field(None, description="Desired intervention type (optional)")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "student_id": "student_001",
                "session_id": "session_001",
                "student_input": "",
                "frontend_signal": None,
                "intervention_type": "hint",
            }
        }


class InterventionResponse(BaseModel):
    """Response model for intervention operations."""

    success: bool = Field(..., description="Operation success status")
    intervention: Optional[Intervention] = Field(None, description="Generated intervention")
    message: str = Field(..., description="Response message")
    breakpoint_location: Optional[dict] = Field(default=None, description="断点位置信息")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "success": True,
                "intervention": None,
                "message": "Intervention generated successfully",
                "breakpoint_location": None,
            }
        }


class FeedbackRequest(BaseModel):
    """处理学生反馈的请求"""

    session_id: str = Field(..., description="Session identifier")
    student_input: str = Field(default="", description="学生提交的新内容")
    frontend_signal: Optional[FrontendSignalEnum] = Field(None, description="前端信号: END / ESCALATE")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_001",
                "student_input": "我不知道下一步怎么走",
                "frontend_signal": None,
            }
        }


class EndRequest(BaseModel):
    """前端触发 END 信号的请求"""

    session_id: str = Field(..., description="Session identifier")
    reason: Optional[str] = Field(None, description="结束原因")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_001",
                "reason": "我知道了"
            }
        }


class EscalateRequest(BaseModel):
    """前端触发 ESCALATE 信号的请求"""

    session_id: str = Field(..., description="Session identifier")
    reason: Optional[str] = Field(None, description="升级原因")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_001",
                "reason": "还是不懂"
            }
        }