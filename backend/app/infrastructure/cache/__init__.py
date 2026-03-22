"""
Cache infrastructure module.

Provides Redis-based caching for improved performance.
"""

from .redis_cache import RedisCache

__all__ = [
    "RedisCache",
]