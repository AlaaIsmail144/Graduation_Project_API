from fastapi import APIRouter, HTTPException, Query

from app.recommendations.api.schemas.responses import (
    InternshipIDsResponse,
    CandidateIDsResponse
)
from app.recommendations.services.recommendation_service import recommendation_service

router = APIRouter()

@router.get(
    "/internships/{candidate_id}/ids",
    response_model=InternshipIDsResponse,
)
async def get_internship_recommendation_ids(
    candidate_id: str,
):
    try:
        recommendations_df, candidate = recommendation_service.get_internship_recommendations(
            candidate_id=candidate_id,
        )
        print('recommendations_df' , recommendations_df)
        if recommendations_df.empty:
            return InternshipIDsResponse(
                candidate_id=candidate_id,
                total=0,
                ids=[]
            )
        internship_ids = [str(iid) for iid in recommendations_df['InternshipId'].tolist()]  # ← InternshipId
        return InternshipIDsResponse(
            candidate_id=candidate_id,
            total=len(internship_ids),
            ids=internship_ids
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/candidates/{internship_id}/ids",
    response_model=CandidateIDsResponse,
)
async def get_candidate_recommendation_ids(
    internship_id: str,
):
    try:
        candidates_df, internship = recommendation_service.get_candidate_recommendations(
            internship_id=internship_id,
        )
        if candidates_df.empty:
            return CandidateIDsResponse(
                internship_id=internship_id,
                total=0,
                ids=[]
            )
        candidate_ids = [str(cid) for cid in candidates_df['candidate_id'].tolist()]
        return CandidateIDsResponse(
            internship_id=internship_id,
            total=len(candidate_ids),
            ids=candidate_ids
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")