####################### Search endpoints #####################

from fastapi import APIRouter, HTTPException
from app.recommendations.api.schemas.requests import SearchInternshipsRequest
from app.recommendations.api.schemas.responses import (
    SearchInternshipsResponse
)
from app.recommendations.services.search_service import search_service

router = APIRouter()

@router.post(
    "/internships/ids",
    response_model=SearchInternshipsResponse,
)
async def search_internships_ids(request: SearchInternshipsRequest):
    try:
        results = search_service.search_internships(
            query=request.query,
            top_k=request.top_k
        )
        
        if not results:
            return SearchInternshipsResponse(
                query=request.query, 
                total=0,
                ids=[]
            )
        internship_ids = [result['internship_id'] for result in results]
        
        return SearchInternshipsResponse(
            query=request.query,  
            total=len(internship_ids),
            ids=internship_ids
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")