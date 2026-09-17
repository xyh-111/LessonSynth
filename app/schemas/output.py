from pydantic import BaseModel, Field
from typing import List, Optional


class TeachingStage(BaseModel):
    stage_name: str = Field(..., description="环节名称，如：情境导入、探究新知、实际运用、总结提升、作业设计")
    steps: List[str] = Field(..., description="该环节的具体教学步骤（教师活动、学生活动）")
    design_intent: str = Field(..., description="【设计意图】教育学依据")
    student_presets: Optional[List[str]] = Field(None, description="学情预设：学生可能的回答")
    teacher_summary: Optional[str] = Field(None, description="教师小结")


class TeachingObjective(BaseModel):
    knowledge: str = Field(..., description="知识与技能目标")
    process: str = Field(..., description="过程与方法目标")
    emotion: str = Field(..., description="情感态度与价值观目标")


class KeyDifficultPoints(BaseModel):
    key_point: str = Field(..., description="教学重点")
    difficult_point: str = Field(..., description="教学难点")


class TeachingDesign(BaseModel):
    pre_class_prep: List[str] = Field(..., description="课前准备")
    teaching_process: List[TeachingStage] = Field(..., description="教学过程（多个环节）")
    blackboard_design: str = Field(..., description="板书设计")
    homework: List[str] = Field(..., description="作业设计")
    teaching_reflection: Optional[str] = Field(None, description="教学研讨/课后反思")


class LessonPlanOutput(BaseModel):
    lesson_title: str = Field(..., description="课时标题")
    teaching_objectives: TeachingObjective = Field(..., description="教学目标（三维）")
    key_difficult_points: KeyDifficultPoints = Field(..., description="重点难点")
    teaching_design: TeachingDesign = Field(..., description="教学案例设计")
