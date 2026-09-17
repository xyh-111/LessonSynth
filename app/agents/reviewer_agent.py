import json

from app.agents.state import AgentState
from app.agents.llm_helper import invoke_structured_llm
from app.schemas.review import ReviewResult


_SYSTEM_PROMPT = """你是一位严格的教案审核专家。请根据课本原文知识点，对生成的教案进行审核。

严格输出以下 JSON 格式，不要输出任何额外文字：
{{
  "pass_review": true,
  "score": 85,
  "issues": [
    {{
      "category": "content_source",
      "stage": "探究新知",
      "description": "问题描述",
      "suggestion": "修改建议"
    }}
  ],
  "overall_comment": "总体审核意见"
}}

审核维度（3个类别）：
1. content_source（内容溯源）：教学内容是否严格来源于课本知识点？是否出现了课本中没有的概念、例题、事实？如有，必须指出并要求删除或替换。
2. format（格式规范）：教案是否包含5个环节（情境导入、探究新知、实际运用、总结提升、作业设计）？每个环节是否有【设计意图】？探究环节是否有学情预设？
3. objective_alignment（目标一致性）：教学过程是否覆盖了所有教学目标？重点难点是否在教学过程中得到突破？

评分规则：
- 90-100：优秀，所有维度达标，无问题
- 70-89：合格，有轻微问题，pass_review=true
- 0-69：不合格，有严重问题（如编造课本内容、缺少环节），pass_review=false

只输出 JSON，不要输出 markdown 代码块标记。"""


def _build_human_prompt(state: AgentState) -> str:
    extracted = state["extracted_textbook"]
    objectives = state["teaching_objectives"]
    key_diff = state["key_difficult_points"]
    stages = state["teaching_stages"]

    kp_text = "\n".join(
        f"- {kp.name}：{kp.description}\n  课本原文：{kp.source_excerpt}"
        for kp in extracted.knowledge_points
    )

    stages_text = ""
    for stage in stages:
        steps_str = "\n".join(f"  - {s}" for s in stage.steps)
        presets_str = "\n".join(f"    · {p}" for p in (stage.student_presets or []))
        stages_text += (
            f"【{stage.stage_name}】\n"
            f"设计意图：{stage.design_intent}\n"
            f"步骤：\n{steps_str}\n"
        )
        if presets_str:
            stages_text += f"学情预设：\n{presets_str}\n"
        if stage.teacher_summary:
            stages_text += f"教师小结：{stage.teacher_summary}\n"
        stages_text += "\n"

    return (
        f"【课本知识点（审核依据）】\n{kp_text}\n\n"
        f"【教学目标】\n"
        f"知识：{objectives.knowledge}\n"
        f"过程：{objectives.process}\n"
        f"情感：{objectives.emotion}\n\n"
        f"【教学重点】{key_diff.key_point}\n"
        f"【教学难点】{key_diff.difficult_point}\n\n"
        f"【教案教学过程】\n{stages_text}\n\n"
        f"请审核以上教案。"
    )


def reviewer_agent(state: AgentState) -> AgentState:
    result = invoke_structured_llm(
        system_prompt=_SYSTEM_PROMPT,
        human_prompt=_build_human_prompt(state),
        output_model=ReviewResult,
    )

    return {
        "review_pass": result.pass_review,
        "review_feedback": result.model_dump(),
    }
