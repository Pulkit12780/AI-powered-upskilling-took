from pydantic import BaseModel
from typing import List


class Skill(BaseModel):
    name: str
    level: str = "unknown"  # beginner / intermediate / advanced / unknown


class SkillList(BaseModel):
    skills: List[Skill]


class TargetSkillList(BaseModel):
    core_skills: List[str]
    soft_skills: List[str]
    tools_and_tech: List[str]


class GapReport(BaseModel):
    strong_skills: List[str]    # present in both, candidate meets or exceeds level
    missing_skills: List[str]   # critical gaps that block hiring
    partial_matches: List[str]  # semantically close but not fully meeting the bar


class CourseRec(BaseModel):
    title: str
    platform: str       # Coursera / Udemy / YouTube
    url: str
    note: str = ""      # "AI-suggested, verify" for LLM recs


class LearningPath(BaseModel):
    weeks: List[dict]   # [{"week": 1, "focus": "...", "resources": [CourseRec]}]
