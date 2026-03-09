from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.recommendations.api.schemas.requests import (
    SyncCandidateRequest,
    SyncInternshipRequest
)
from app.recommendations.api.schemas.responses import SyncResponse
from app.recommendations.services.sync_service import sync_service
from datetime import datetime

router = APIRouter( )


@router.post(
    "/candidate",
    response_model=SyncResponse,
)
async def sync_candidate(request: SyncCandidateRequest, background_tasks: BackgroundTasks):

    try:
        background_tasks.add_task(
            sync_service.process_add_candidate_bg,
            request.candidate_id
        )

        return SyncResponse(
            success=True,
            candidate_id=request.candidate_id,
            message="candidate sync task queued successfully. Processing in background.",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"failed to queue candidate sync task: {str(e)}"
        )


@router.post(
    "/internship",
    response_model=SyncResponse,

)
async def sync_internship(request: SyncInternshipRequest, background_tasks: BackgroundTasks):
    
    try:
        background_tasks.add_task(
            sync_service.process_add_internship_bg,
            request.internship_id
        )
    
        return SyncResponse(
            success=True,
            internship_id=request.internship_id,
            message="internship sync task queued successfully. Processing in background.",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue internship sync task: {str(e)}"
        )


@router.delete(
    "/candidate/{candidate_id}",
    response_model=SyncResponse,
)
async def delete_candidate(candidate_id: str, background_tasks: BackgroundTasks):
   
    try:

        background_tasks.add_task(
            sync_service.process_delete_candidate_bg,
            candidate_id
        )

        return SyncResponse(
            success=True,
            candidate_id=candidate_id,
            message="candidate deletion task queued successfully. Processing in background.",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"failed to queue candidate deletion task: {str(e)}"
        )


@router.delete(
    "/internship/{internship_id}",
    response_model=SyncResponse,
)
async def delete_internship(internship_id: str, background_tasks: BackgroundTasks):
   
    try:
        background_tasks.add_task(
            sync_service.process_delete_internship_bg,
            internship_id
        )
        
        return SyncResponse(
            success=True,
            internship_id=internship_id,
            message="internship deletion task queued successfully. Processing in background.",
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"failed to queue internship deletion task: {str(e)}"
        )