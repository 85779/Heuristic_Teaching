"""
公共响应模型
"""

from pydantic import BaseModel
from typing import Any, Optional


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "OK"
    

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error_code: str
    error_message: str
    details: Optional[dict[str, Any]] = None