####################### Search endpoints #####################

from fastapi import APIRouter, HTTPException
from app.recommendations.api.schemas.requests import SearchInternshipsRequest
from app.recommendations.api.schemas.responses import (
    SearchInternshipsResponse,
    InternshipSearchResult,
    InternshipIDsResponse
)
from app.recommendations.services.search_service import search_service

router = APIRouter()


@router.post(
    "/internships",
    response_model=SearchInternshipsResponse,
    summary="Semantic search for internships"
)
async def search_internships(request: SearchInternshipsRequest):
    
    try:
        results = search_service.search_internships(
            query=request.query,
            location=request.location,
            duration=request.duration,
            top_k=request.top_k
        )
    
        search_results = [
            InternshipSearchResult(**result)
            for result in results
        ]
        
        return SearchInternshipsResponse(
            query=request.query,
            total_results=len(search_results),
            results=search_results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post(
    "/internships/ids",
    response_model=InternshipIDsResponse,
)
async def search_internships_ids(request: SearchInternshipsRequest):
    try:
        results = search_service.search_internships(
            query=request.query,
            location=None,
            duration=None,
            top_k=request.top_k
        )
        
        if not results:
            return InternshipIDsResponse(
                candidate_id=request.query, 
                total=0,
                ids=[]
            )
        internship_ids = [result['internship_id'] for result in results]
        
        return InternshipIDsResponse(
            candidate_id=request.query,  
            total=len(internship_ids),
            ids=internship_ids
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")