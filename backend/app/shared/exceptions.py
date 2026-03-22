"""
自定义异常
"""


class MathTutorException(Exception):
    """基础异常类"""
    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ModuleNotFoundError(MathTutorException):
    """模块未找到"""
    def __init__(self, module_id: str):
        super().__init__(
            message=f"Module '{module_id}' not found",
            code="MODULE_NOT_FOUND"
        )


class SessionNotFoundError(MathTutorException):
    """会话未找到"""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found",
            code="SESSION_NOT_FOUND"
        )


class LLMError(MathTutorException):
    """LLM调用错误"""
    def __init__(self, message: str, provider: str = "unknown"):
        super().__init__(
            message=f"LLM error ({provider}): {message}",
            code="LLM_ERROR"
        )


class PipelineError(MathTutorException):
    """Pipeline执行错误"""
    def __init__(self, step: str, message: str):
        super().__init__(
            message=f"Pipeline error at step '{step}': {message}",
            code="PIPELINE_ERROR"
        )