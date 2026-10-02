from pydantic import BaseModel ,Field
from typing import Optional ,List
from datetime import datetime

class AnalysisRequest(BaseModel):
    job_description:str = Field(...,min_length=50, max_length=5000)
    
class KeywordMatch(BaseModel):
    keyword: str
    found: str
    context: Optional[str]= None
    
class AnalysisResult(BaseModel):
    overall_score: float
    keyword_score: float
    experience_score:float
    skills_score:float
    keywords_found: list[KeywordMatch]
    strengths:List[str]
    weaknesses:List[str]
    suggestions:List[str]
    summary:str
    
class AnalysisResponse(BaseModel):
    id:int
    resume_filename:str
    overall_score:float
    status:str
    result:Optional[AnalysisResult]=None
    created_at:datetime

    class Config:
        from_attributes = True




