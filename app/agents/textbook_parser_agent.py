from app.agents.state import AgentState
from app.tools import extract_knowledge


def textbook_parser_agent(state: AgentState) -> AgentState:
    textbook_input = state["textbook_input"]
    extracted = extract_knowledge(textbook_input.textbook_content)
    return {"extracted_textbook": extracted}
