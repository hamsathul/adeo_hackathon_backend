# app/schemas/search.py
from pydantic import BaseModel
from typing import List, Dict, Optional

class SearchRequest(BaseModel):
    query: str
    options: Optional[List[str]] = None

class SearchResponse(BaseModel):
    success: bool
    results: Dict
    error: Optional[str] = None