"""Bug report model."""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class BugReport:
    """Bug report data model."""
    title: str
    summary: str
    root_cause: str
    severity: str  # critical, high, medium, low
    affected_files: List[str]
    reproduction_steps: str
    impact: str
    created_at: datetime = datetime.now()
    
    def to_dict(self):
        return {
            'title': self.title,
            'summary': self.summary,
            'root_cause': self.root_cause,
            'severity': self.severity,
            'affected_files': self.affected_files,
            'reproduction_steps': self.reproduction_steps,
            'impact': self.impact,
            'created_at': self.created_at.isoformat()
        }