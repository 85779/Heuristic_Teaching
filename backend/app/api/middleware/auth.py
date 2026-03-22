"""
认证中间件
"""


class AuthMiddleware:
    """认证中间件"""

    def __init__(self, app):
        """初始化中间件"""
        self.app = app

    async def __call__(self, scope, receive, send):
        """ASGI 调用方法"""
        raise NotImplementedError("AuthMiddleware not implemented yet")