# app/api/v1/endpoints/search.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
from app.schemas.search import SearchRequest, SearchResponse
from app.core.serpsearch.serpapi import SerperClient

router = APIRouter()

@router.post("/", response_model=SearchResponse)
async def perform_search(
    search_request: SearchRequest,
    serper_client: SerperClient = Depends(lambda: SerperClient())
):
    try:
        results = {}
        
        # If no options provided, perform default search
        if not search_request.options:
            search_result = await serper_client.search(search_request.query)
            results['search'] = search_result
        else:
            # Process all selected options
            for option in search_request.options:
                search_result = await serper_client.search(search_request.query, option)
                results[option] = search_result

        return SearchResponse(
            success=True,
            results=results
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )