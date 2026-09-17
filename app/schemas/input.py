from pydantic import BaseModel, Field
from typing import Optional


class TextbookInput(BaseModel):
    subject: str = Field(..., description="学科，如：数学")
    grade: str = Field(..., description="年级，如：四年级")
    unit: Optional[str] = Field(None, description="单元，如：第一单元")
    lesson_title: str = Field(..., description="课时标题，如：从结绳计数说起")
    duration: str = Field("1课时", description="课时长度")
    textbook_content: Optional[str] = Field(None, description="课本原文内容（可直接输入，或通过文件上传解析获得）")
