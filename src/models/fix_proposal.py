"""Fix proposal model."""
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class CodeChange:
    """Individual code change."""
    file_path: str
    original_code: str
    fixed_code: str
    line_start: int
    line_end: int
    explanation: str

@dataclass
class FixProposal:
    """Fix proposal data model."""
    primary_fix: CodeChange
    alternative_fixes: List[CodeChange]
    explanation: str
    considerations: List[str]
    test_requirements: List[str]
    
    def to_dict(self):
        return {
            'primary_fix': {
                'file_path': self.primary_fix.file_path,
                'original_code': self.primary_fix.original_code,
                'fixed_code': self.primary_fix.fixed_code,
                'line_start': self.primary_fix.line_start,
                'line_end': self.primary_fix.line_end,
                'explanation': self.primary_fix.explanation
            },
            'alternative_fixes': [
                {
                    'file_path': fix.file_path,
                    'original_code': fix.original_code,
                    'fixed_code': fix.fixed_code,
                    'explanation': fix.explanation
                }
                for fix in self.alternative_fixes
            ],
            'explanation': self.explanation,
            'considerations': self.considerations,
            'test_requirements': self.test_requirements
        }