# app/api/v1/endpoints/googlecrew.py
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from app.core.googlesearchcrew.searchtopicscrew import GoogleSearchCrew
import json

router = APIRouter()

class NewsArticle(BaseModel):
    title: str
    source: str
    date: str
    url: str
    summary: str

class Trend(BaseModel):
    trend_name: str
    description: str

class ResearchData(BaseModel):
    topic: str
    description: str
    keywords: List[str]
    latest_news: List[NewsArticle]
    trends: List[Trend]

class ResearchRequest(BaseModel):
    query: str
    async_execution: Optional[bool] = False

class ResearchResponse(BaseModel):
    task_id: Optional[str] = None
    data: Optional[ResearchData] = None
    status: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    data: Optional[ResearchData] = None
    error: Optional[str] = None

# In-memory storage for task results
task_results = {}

def clean_json_string(json_str: str) -> str:
    """Clean the JSON string by removing markdown formatting and timestamps"""
    if isinstance(json_str, dict):  # If already parsed, return as is
        return json_str
        
    # Remove markdown formatting
    json_str = json_str.replace('```json', '').replace('```', '')
    
    # Remove timestamps and debug information
    lines = json_str.split('\n')
    clean_lines = []
    for line in lines:
        # Skip timestamp lines and debug lines
        if line.strip().startswith('2024-') or line.strip().startswith('[DEBUG]'):
            continue
        clean_lines.append(line)
    
    return '\n'.join(clean_lines)

async def execute_research(task_id: str, request: ResearchRequest):
    try:
        crew = GoogleSearchCrew(query=request.query)
        results = crew.crew().kickoff()
        
        # Clean and parse the JSON
        cleaned_results = clean_json_string(results)
        parsed_results = json.loads(cleaned_results)
        
        task_results[task_id] = {
            "status": "completed",
            "data": parsed_results
        }
    except Exception as e:
        task_results[task_id] = {
            "status": "failed",
            "error": str(e)
        }

@router.post("/analyze", response_model=ResearchResponse)
async def analyze_topic(request: ResearchRequest, background_tasks: BackgroundTasks):
    try:
        # Validate query
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        if request.async_execution:
            task_id = f"task_{len(task_results) + 1}"
            task_results[task_id] = {"status": "pending"}
            background_tasks.add_task(execute_research, task_id, request)
            
            return ResearchResponse(
                task_id=task_id,
                status="pending"
            )
        else:
            crew = GoogleSearchCrew(query=request.query)
            results = crew.crew().kickoff()
            
            # Clean and parse the JSON
            cleaned_results = clean_json_string(results)
            parsed_results = json.loads(cleaned_results)
            
            return ResearchResponse(
                data=parsed_results,
                status="completed"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    if task_id not in task_results:
        raise HTTPException(status_code=404, detail="Task not found")
        
    task_info = task_results[task_id]
    
    if task_info["status"] == "failed":
        return TaskStatus(
            task_id=task_id,
            status="failed",
            error=task_info.get("error")
        )
    
    return TaskStatus(
        task_id=task_id,
        status=task_info["status"],
        data=task_info.get("data")
    )