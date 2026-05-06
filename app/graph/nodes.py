from openai import OpenAI
from pydantic import BaseModel
from typing import List
from app.config import settings
from app.schemas import SkillList, TargetSkillList, GapReport, LearningPath, CourseRec
from app.graph.state import GraphState
from app.youtube import search_videos

client = OpenAI(api_key=settings.openai_api_key)


class _CourseItem(BaseModel):
    title: str
    platform: str
    url: str


class _WeekPlan(BaseModel):
    week: int
    focus: str
    courses: List[_CourseItem]
    youtube_queries: List[str]


class _WeekPlanList(BaseModel):
    weeks: List[_WeekPlan]


def extract_skills(state: GraphState) -> GraphState:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a resume parser. Extract every professional skill mentioned "
                    "from the summary (if provided), roles and responsibilities in college "
                    "(if not more than 2 years old), work experience, and any technical skills "
                    "mentioned in the resume. Include technical skills, tools, frameworks, "
                    "soft skills, and domain knowledge. Estimate proficiency level based on "
                    "context clues (years of experience, job titles, project descriptions)."
                ),
            },
            {
                "role": "user",
                "content": f"Extract skills from this resume:\n\n{state['resume_text']}",
            },
        ],
        response_format=SkillList,
    )
    state["current_skills"] = response.choices[0].message.parsed
    return state


def target_skills(state: GraphState) -> GraphState:
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert in job analysis, skill taxonomy, and competency frameworks. "
                    "Your job is to extract the industry-standard skill set required for a given "
                    "target job role. Categorize skills under core_skills (role-specific hard skills), "
                    "soft_skills, and tools_and_tech. Keep skill names concise and standardized. "
                    "Include 12-20 relevant skills total. No explanations, no extra text."
                ),
            },
            {
                "role": "user",
                "content": f"List all required skills for: {state['target_role']}",
            },
        ],
        response_format=TargetSkillList,
    )
    state["required_skills"] = response.choices[0].message.parsed
    return state


def gap_diff(state: GraphState) -> GraphState:
    current = state["current_skills"]
    required = state["required_skills"]

    current_text = "\n".join(
        f"- {s.name} ({s.level})" for s in current.skills
    )
    required_lines = (
        [f"- {s} (core)" for s in required.core_skills]
        + [f"- {s} (soft)" for s in required.soft_skills]
        + [f"- {s} (tool/tech)" for s in required.tools_and_tech]
    )
    required_text = "\n".join(required_lines)

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a career coach. Compare a candidate's current skills against "
                    "the skills required for their target role. The skills required can be fetched "
                    "from LinkedIn, Indeed, naukri.com or any other website relevant for that location. "
                    "Please ensure that you are looking at the websites for the given location. "
                    "For example: a skill might be required for a PM in India but not in Europe or vice versa. "
                    "Classify each required skill into one of three buckets:\n"
                    "- strong_skills: candidate clearly has this skill at or above the required level\n"
                    "- missing_skills: critical gap that will block hiring\n"
                    "- partial_matches: candidate has a related skill but not at the required level\n"
                    "Be concise. Use exact skill names from the provided lists. Do NOT hallucinate."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Current skills:\n{current_text}\n\n"
                    f"Required skills for the role:\n{required_text}"
                    + (f"\n\nCandidate's target location: {state['location']}" if state.get("location") else "")
                ),
            },
        ],
        response_format=GapReport,
    )
    state["gap_report"] = response.choices[0].message.parsed
    return state


def recommend(state: GraphState) -> GraphState:
    gap = state["gap_report"]
    target_role = state["target_role"]

    skills_to_address = gap.missing_skills + gap.partial_matches
    if not skills_to_address:
        state["learning_path"] = LearningPath(weeks=[])
        return state

    skills_text = "\n".join(
        [f"- {s} (missing — critical gap)" for s in gap.missing_skills]
        + [f"- {s} (partial — needs strengthening)" for s in gap.partial_matches]
    )

    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a career coach. Given skill gaps for a target role, build a "
                    "realistic 2–4 week learning plan. For each week:\n"
                    "- Set a clear focus theme grouping related skills.\n"
                    "- Suggest 2–3 specific courses from Coursera or Udemy (use real course "
                    "names; set url to '' if you are not certain of the exact URL).\n"
                    "- Provide 2 YouTube search queries that would surface the best free "
                    "tutorials for that week's skills.\n"
                    "Prioritise missing skills in early weeks. Keep weeks achievable (~5–8 "
                    "hours each)."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Target role: {target_role}\n\n"
                    f"Skills to address:\n{skills_text}"
                ),
            },
        ],
        response_format=_WeekPlanList,
    )

    plan = response.choices[0].message.parsed

    weeks_output = []
    for week_plan in plan.weeks:
        resources: list[CourseRec] = [
            CourseRec(
                title=c.title,
                platform=c.platform,
                url=c.url,
                note="AI-suggested — verify before enrolling",
            )
            for c in week_plan.courses
        ]

        for query in week_plan.youtube_queries[:2]:
            try:
                yt_results = search_videos(query, max_results=2)
                resources.extend(yt_results)
            except Exception:
                pass

        weeks_output.append({
            "week": week_plan.week,
            "focus": week_plan.focus,
            "resources": resources,
        })

    state["learning_path"] = LearningPath(weeks=weeks_output)
    return state
