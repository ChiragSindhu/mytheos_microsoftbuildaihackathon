"""Pull request template model."""
from dataclasses import dataclass
from typing import List

@dataclass
class PullRequestTemplate:
    """Pull request template."""
    title: str
    description: str
    files_changed: List[str]
    tests_added: List[str]
    review_checklist: List[str]
    related_issues: List[str]
    
    def to_markdown(self) -> str:
        """Generate PR markdown."""
        md = f"# {self.title}\n\n"
        md += f"## Description\n{self.description}\n\n"
        md += f"## Files Changed\n"
        for file in self.files_changed:
            md += f"- {file}\n"
        md += f"\n## Tests Added\n"
        for test in self.tests_added:
            md += f"- {test}\n"
        md += f"\n## Review Checklist\n"
        for item in self.review_checklist:
            md += f"- [ ] {item}\n"
        return md