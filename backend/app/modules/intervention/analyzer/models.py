from dataclasses import dataclass, field
from typing import List


@dataclass
class BreakpointAnalysis:
    """Analysis result for what is needed to cross a breakpoint."""
    required_knowledge: List[str] = field(default_factory=list)
    """Knowledge/skills needed to cross this breakpoint"""
    
    required_connection: str = ""
    """The key connection or relationship that needs to be established"""
    
    possible_approaches: List[str] = field(default_factory=list)
    """Alternative approaches to cross this breakpoint"""
    
    difficulty_level: float = 0.5
    """Difficulty level 0.0~1.0"""
