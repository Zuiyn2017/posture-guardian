"""
响应数据模型
"""
from typing import List, Optional
from pydantic import BaseModel


class PostureAnalysisResult(BaseModel):
    """坐姿分析结果模型"""
    status: str  # "normal" | "no_person" | "not_writing"
    score: int  # 0-100
    is_qualified: bool
    issues: List[str]
    suggestion: str


class DetectionResponse(BaseModel):
    """检测响应模型"""
    status: str
    score: int
    is_qualified: bool
    issues: List[str]
    suggestion: str
    audio: Optional[str] = None
    raw_result: dict

