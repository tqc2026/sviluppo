from dataclasses import dataclass, field
from typing import List


@dataclass
class ProjectBrief:
    client_name: str = ""
    project_name: str = ""
    client_sector: str = ""
    project_types: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    content_source: str = ""
    has_brand: bool = False
    brand_assets: List[str] = field(default_factory=list)
    needs_brand_creation: bool = False
    approval_workflow: bool = True
    posts_frequency: str = ""
    target_audience: str = ""
    phase2_goals: str = ""
    needs_landing_page: bool = False
    needs_email_marketing: bool = False
    timeline: str = ""
    budget_hint: str = ""
    special_notes: str = ""
    raw_summary: str = ""
