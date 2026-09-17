from langgraph.graph import StateGraph, END

from app.agents.state import AgentState
from app.agents.textbook_parser_agent import textbook_parser_agent
from app.agents.objective_agent import objective_agent, key_difficult_agent
from app.agents.process_agent import process_agent
from app.agents.reviewer_agent import reviewer_agent

MAX_REVISIONS = 2


def _review_route(state: AgentState) -> str:
    if state.get("review_pass"):
        return "end"
    revision_count = state.get("revision_count", 0)
    if revision_count >= MAX_REVISIONS:
        return "end"
    return "revise"


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("textbook_parser", textbook_parser_agent)
    graph.add_node("objective", objective_agent)
    graph.add_node("key_difficult", key_difficult_agent)
    graph.add_node("process", process_agent)
    graph.add_node("reviewer", reviewer_agent)

    graph.set_entry_point("textbook_parser")
    graph.add_edge("textbook_parser", "objective")
    graph.add_edge("objective", "key_difficult")
    graph.add_edge("key_difficult", "process")
    graph.add_edge("process", "reviewer")

    graph.add_conditional_edges(
        "reviewer",
        _review_route,
        {
            "revise": "process",
            "end": END,
        },
    )

    return graph.compile()
