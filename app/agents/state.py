from typing import TypedDict, Optional, List, Dict, Any

from app.schemas.input import TextbookInput
from app.schemas.textbook import ExtractedTextbook
from app.schemas.output import (
    TeachingObjective,
    KeyDifficultPoints,
    TeachingStage,
    TeachingDesign,
    LessonPlanOutput,
)


class AgentState(TypedDict, total=False):
    textbook_input: TextbookInput
    extracted_textbook: ExtractedTextbook
    teaching_objectives: TeachingObjective
    key_difficult_points: KeyDifficultPoints
    teaching_stages: List[TeachingStage]
    blackboard_design: str
    homework: List[str]
    teaching_reflection: str
    final_output: LessonPlanOutput
    review_pass: Optional[bool]
    review_feedback: Optional[Dict[str, Any]]
    revision_count: int
