from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.nodes import extract_skills, target_skills, gap_diff, recommend


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("extract_skills", extract_skills)
    g.add_node("target_skills", target_skills)
    g.add_node("gap_diff", gap_diff)
    g.add_node("recommend", recommend)

    g.set_entry_point("extract_skills")
    g.add_edge("extract_skills", "target_skills")
    g.add_edge("target_skills", "gap_diff")
    g.add_edge("gap_diff", "recommend")
    g.add_edge("recommend", END)

    return g.compile()


graph = build_graph()
