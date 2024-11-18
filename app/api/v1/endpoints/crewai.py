# app/api/v1/endpoints/crewai.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.researchcrew.crew import AIResearchCrew

router = APIRouter()

class ResearchRequest(BaseModel):
    query: str

class ResearchResponse(BaseModel):
    research_findings: str

@router.post("/analyze", response_model=ResearchResponse)
async def analyze_topic(request: ResearchRequest):
    try:
        crew = AIResearchCrew(request.query)
        result = crew.run()
        return ResearchResponse(research_findings=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))