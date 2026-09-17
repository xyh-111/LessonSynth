from pydantic import BaseModel, Field
from typing import List, Optional


class ExampleItem(BaseModel):
    content: str = Field(..., description="例题内容")
    answer: Optional[str] = Field(None, description="例题答案/解析")


class ExerciseItem(BaseModel):
    content: str = Field(..., description="习题内容")


class KnowledgePoint(BaseModel):
    name: str = Field(..., description="知识点名称，如：自然数的概念")
    description: str = Field(..., description="知识点描述")
    source_excerpt: str = Field(..., description="课本中对应的原文片段")


class ExtractedTextbook(BaseModel):
    lesson_title: str = Field(..., description="课时标题")
    knowledge_points: List[KnowledgePoint] = Field(..., description="核心知识点列表")
    examples: List[ExampleItem] = Field(default_factory=list, description="例题列表")
    exercises: List[ExerciseItem] = Field(default_factory=list, description="习题列表")
    key_terms: List[str] = Field(default_factory=list, description="关键概念/术语")
    summary: str = Field(..., description="课本内容摘要")
