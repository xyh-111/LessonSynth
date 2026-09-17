from app.agents.state import AgentState
from app.agents.llm_helper import invoke_structured_llm
from app.schemas.output import TeachingObjective, KeyDifficultPoints


_SYSTEM_PROMPT_OBJECTIVES = """你是一位资深的教学设计专家。请根据课本知识点和课程标准，为本节课设计三维教学目标。

严格输出以下 JSON 格式，不要输出任何额外文字：
{{
  "knowledge": "知识与技能目标",
  "process": "过程与方法目标",
  "emotion": "情感态度与价值观目标"
}}

要求：
1. knowledge：学生需要掌握的知识和技能，必须来源于课本知识点。
2. process：学生通过什么过程与方法（观察、操作、交流、探究等）达成目标。
3. emotion：培养学生的情感态度与价值观（如热爱数学、体会数学文化等）。
目标要具体、可达成，符合{grade}{subject}学段学生特点。只输出 JSON。"""


_SYSTEM_PROMPT_KEYDIFF = """你是一位资深的教学设计专家。请根据课本知识点，确定本节课的教学重点和难点。

严格输出以下 JSON 格式，不要输出任何额外文字：
{{
  "key_point": "教学重点",
  "difficult_point": "教学难点"
}}

要求：
1. key_point：教学重点是本节课必须掌握的核心知识和技能。
2. difficult_point：教学难点是学生难以理解或容易混淆的内容，通常是抽象性强或需要思维转化的知识点。
只输出 JSON。"""


def objective_agent(state: AgentState) -> AgentState:
    textbook_input = state["textbook_input"]
    extracted = state["extracted_textbook"]

    kp_text = "\n".join(
        f"- {kp.name}: {kp.description}" for kp in extracted.knowledge_points
    )

    objectives = invoke_structured_llm(
        system_prompt=_SYSTEM_PROMPT_OBJECTIVES,
        human_prompt=(
            f"课题：{extracted.lesson_title}\n"
            f"学段：{textbook_input.grade}{textbook_input.subject}\n"
            f"核心知识点：\n{kp_text}\n\n"
            f"请设计三维教学目标。"
        ),
        output_model=TeachingObjective,
        grade=textbook_input.grade,
        subject=textbook_input.subject,
    )

    return {"teaching_objectives": objectives}


def key_difficult_agent(state: AgentState) -> AgentState:
    extracted = state["extracted_textbook"]

    kp_text = "\n".join(
        f"- {kp.name}: {kp.description}" for kp in extracted.knowledge_points
    )

    key_diff = invoke_structured_llm(
        system_prompt=_SYSTEM_PROMPT_KEYDIFF,
        human_prompt=(
            f"课题：{extracted.lesson_title}\n"
            f"核心知识点：\n{kp_text}\n\n"
            f"请确定教学重点和难点。"
        ),
        output_model=KeyDifficultPoints,
    )

    return {"key_difficult_points": key_diff}
