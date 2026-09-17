from pydantic import BaseModel, Field
from typing import List, Optional


class ReviewIssue(BaseModel):
    category: str = Field(..., description="问题类别：content_source / format / objective_alignment")
    stage: Optional[str] = Field(None, description="出问题的环节名称，如全局问题则为null")
    description: str = Field(..., description="问题描述")
    suggestion: str = Field(..., description="修改建议")


class ReviewResult(BaseModel):
    pass_review: bool = Field(..., description="是否通过审核")
    score: int = Field(..., description="综合评分（0-100）")
    issues: List[ReviewIssue] = Field(default_factory=list, description="问题列表")
    overall_comment: str = Field(..., description="总体审核意见")
