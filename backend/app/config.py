"""
全局配置
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "Math Tutor"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # MongoDB 配置
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "math_tutor"
    
    # LLM 配置
    LLM_PROVIDER: str = "openai"  # openai | anthropic | dashscope
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    
    # DashScope 配置 (阿里云百炼)
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    # 各模块使用的模型
    SOLVING_MODEL: str = "qwen-turbo"         # 模块一：组织化解主治线
    INTERVENTION_MODEL: str = "qwen-turbo"     # 模块二：断点干预
    
    # Redis 配置 (可选)
    REDIS_URL: Optional[str] = None
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()