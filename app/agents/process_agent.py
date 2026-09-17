from typing import List, Dict, Any

from app.agents.state import AgentState
from app.agents.llm_helper import invoke_structured_llm
from app.schemas.output import TeachingStage, TeachingDesign


_SYSTEM_PROMPT = """你是一位资深的小学数学教学设计专家。请根据课本内容、教学目标和重难点，设计完整的教学过程。

请严格输出以下 JSON 格式，不要输出任何额外文字：

{{
  "pre_class_prep": ["课前准备项1", "课前准备项2"],
  "teaching_process": [
    {{
      "stage_name": "环节名称",
      "steps": ["教学步骤1", "教学步骤2"],
      "design_intent": "该环节的设计意图（教育学依据）",
      "student_presets": ["学情预设1", "学情预设2"],
      "teacher_summary": "教师小结"
    }}
  ],
  "blackboard_design": "板书设计（结构化文本）",
  "homework": ["作业1", "作业2"],
  "teaching_reflection": "教学研讨/课后反思"
}}

教学过程必须包含以下5个环节（顺序固定）：
1. 情境导入：通过视频、故事、问题等激发学生兴趣，引出课题。
2. 探究新知：包含2-3个任务，引导学生探究核心知识点，每个任务要有教师引导、学生活动、学情预设、教师小结。
3. 实际运用：通过教材习题或生活实例巩固所学知识。
4. 总结提升：引导学生总结本节课收获，并提出后续思考。
5. 作业设计：布置分层作业（基础+拓展）。

重要要求：
1. 所有教学内容必须严格来源于课本知识点，不得编造课本没有的内容。
2. 每个环节都要有【设计意图】。
3. 探究新知环节必须有学情预设（学生可能的回答）。
4. 步骤要具体到教师说什么、学生做什么。
5. 板书设计要结构化、有层次。
只输出 JSON，不要输出 markdown 代码块标记。"""


def _build_human_prompt(state: AgentState) -> str:
    textbook_input = state["textbook_input"]
    extracted = state["extracted_textbook"]
    objectives = state["teaching_objectives"]
    key_diff = state["key_difficult_points"]

    kp_text = "\n".join(
        f"- {kp.name}：{kp.description}\n  原文：{kp.source_excerpt}"
        for kp in extracted.knowledge_points
    )

    prompt = (
        f"课题：{extracted.lesson_title}\n"
        f"学科年级：{textbook_input.grade}{textbook_input.subject}\n"
        f"课时：{textbook_input.duration}\n\n"
        f"【课本核心知识点】\n{kp_text}\n\n"
        f"【教学目标】\n"
        f"知识与技能：{objectives.knowledge}\n"
        f"过程与方法：{objectives.process}\n"
        f"情感态度：{objectives.emotion}\n\n"
        f"【教学重点】{key_diff.key_point}\n"
        f"【教学难点】{key_diff.difficult_point}\n\n"
    )

    review_feedback = state.get("review_feedback")
    if review_feedback and review_feedback.get("issues"):
        issues = review_feedback["issues"]
        prompt += "【审核反馈（请根据以下意见修改教案）】\n"
        for issue in issues:
            prompt += f"- [{issue['category']}] {issue['description']}\n  建议：{issue['suggestion']}\n"
        prompt += "\n请根据以上审核意见修改并重新输出完整教案。\n"
    else:
        prompt += "请设计完整的教学过程。"

    return prompt


def process_agent(state: AgentState) -> AgentState:
    data = invoke_structured_llm(
        system_prompt=_SYSTEM_PROMPT,
        human_prompt=_build_human_prompt(state),
        output_model=TeachingDesign,
    )

    current_revision = state.get("revision_count", 0)
    stages = data.teaching_process
    return {
        "teaching_stages": stages,
        "blackboard_design": data.blackboard_design,
        "homework": data.homework,
        "teaching_reflection": data.teaching_reflection,
        "revision_count": current_revision + 1,
    }
