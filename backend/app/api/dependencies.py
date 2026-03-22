"""
API 依赖注入
"""

from typing import Generator
from app.core.registry.module_registry import ModuleRegistry
from app.core.state.session_manager import SessionManager


# 全局实例 (在应用启动时初始化)
_module_registry: ModuleRegistry | None = None
_session_manager: SessionManager | None = None


def get_module_registry() -> ModuleRegistry:
    """获取模块注册器"""
    if _module_registry is None:
        raise RuntimeError("ModuleRegistry not initialized")
    return _module_registry


def get_session_manager() -> SessionManager:
    """获取会话管理器"""
    if _session_manager is None:
        raise RuntimeError("SessionManager not initialized")
    return _session_manager