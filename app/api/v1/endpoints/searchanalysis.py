from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.ai.searchanalysis import ResearchAnalyzer

router = APIRouter()

class SearchRequest(BaseModel):
   query: str

class SearchResponse(BaseModel):
   results: dict

@router.post("/search")
async def search_topic(request: SearchRequest):
   try:
       analyzer = ResearchAnalyzer(query=request.query)
       results = await analyzer.analyze()
       return SearchResponse(results=results)
   except Exception as e:
       raise HTTPException(
           status_code=500,
           detail=f"Search failed: {str(e)}"
       )