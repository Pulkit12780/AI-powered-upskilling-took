from typing import TypedDict, Optional
from app.schemas import SkillList, TargetSkillList, GapReport, LearningPath


class GraphState(TypedDict):
    resume_text: str
    target_role: str
    location: Optional[str]
    current_skills: Optional[SkillList]
    required_skills: Optional[TargetSkillList]
    gap_report: Optional[GapReport]
    learning_path: Optional[LearningPath]
    error: Optional[str]
