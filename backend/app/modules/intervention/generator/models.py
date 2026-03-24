"""Data models for the intervention generator module."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GeneratedHint:
    """Generated intervention hint."""
    content: str
    """The hint content text"""
    
    level: str
    """Level: 'surface' (intensity<0.4), 'middle' (0.4<=intensity<0.7), 'deep' (intensity>=0.7)"""
    
    approach_used: str
    """The approach used to cross the breakpoint"""
    
    original_intensity: float
    """The original intensity value provided"""
