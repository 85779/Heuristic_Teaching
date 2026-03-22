"""
错误处理中间件
"""


class ErrorHandlerMiddleware:
    """错误处理中间件"""

    def __init__(self, app):
        """初始化中间件"""
        self.app = app

    async def __call__(self, scope, receive, send):
        """ASGI 调用方法"""
        raise NotImplementedError("ErrorHandlerMiddleware not implemented yet")