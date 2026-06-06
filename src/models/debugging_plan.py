"""Debugging plan model."""
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class DebuggingPlan:
    """Debugging plan data model."""
    error_classification: str
    affected_components: List[str]
    investigation_strategy: List[str]
    reproduction_steps: List[str]
    hypotheses: List[str]
    suggested_approach: str
    
    def to_dict(self):
        return {
            'error_classification': self.error_classification,
            'affected_components': self.affected_components,
            'investigation_strategy': self.investigation_strategy,
            'reproduction_steps': self.reproduction_steps,
            'hypotheses': self.hypotheses,
            'suggested_approach': self.suggested_approach
        }