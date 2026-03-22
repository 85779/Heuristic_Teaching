"""
会话请求/响应模型
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SessionCreate(BaseModel):
    """创建会话请求"""
    student_id: Optional[str] = None
    problem_content: str


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    status: str
    created_at: datetime
    current_phase: Optional[str] = None