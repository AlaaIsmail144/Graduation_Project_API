from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from uuid import UUID
import uuid
from datetime import datetime
from typing import Dict, Any
import numpy as np

from app.internship.models.schemas import (
    InternshipIDRequest,
    InternshipIDsRequest,
    AssignmentResult,
    BatchAssignmentResponse
)
from app.internship.services.assignment import AssignmentService

router = APIRouter()

single_assignment_jobs: Dict[str, Dict[str, Any]] = {}
batch_assignment_jobs: Dict[str, Dict[str, Any]] = {}

def convert_numpy_types(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def run_batch_assignment_job(job_id: str, internship_ids: list):  
    try:
        batch_assignment_jobs[job_id]["status"] = "running"
        batch_assignment_jobs[job_id]["started_at"] = datetime.now()
        print(f"\n Starting batch assignment job {job_id}...")
        
        assignment_service = AssignmentService()
        result = assignment_service.assign_batch_internships(internship_ids)
        result = convert_numpy_types(result)
        
        batch_assignment_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "result": result,
            "error": None
        })
        print(f"\n Job {job_id} completed successfully!")
        
    except Exception as e:
        batch_assignment_jobs[job_id].update({
            "status": "failed",
            "completed_at": datetime.now(),
            "error": str(e)
        })
        print(f"\n Job {job_id} failed: {str(e)}")

def run_single_assignment_job(job_id: str, internship_id: UUID):

    try:
        single_assignment_jobs[job_id]["status"] = "running"
        single_assignment_jobs[job_id]["started_at"] = datetime.now()
        print(f"\n Starting single assignment job {job_id} for internship {internship_id}...")
        
        assignment_service = AssignmentService()
        result = assignment_service.assign_single_internship(internship_id)
        
        if not result:
            single_assignment_jobs[job_id].update({
                "status": "failed",
                "completed_at": datetime.now(),
                "error": "Internship not found, has insufficient text, or no matching topic available"
            })
            print(f"\n OPPs!!!  Job {job_id} failed: Internship not found or no topic match")
            return
        result = convert_numpy_types(result)

        single_assignment_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "result": result,
            "error": None
        })
        print(f"\nDone! Job {job_id} completed successfully")
        
    except Exception as e:
        single_assignment_jobs[job_id].update({
            "status": "failed",
            "completed_at": datetime.now(),
            "error": str(e)
        })
        print(f"\nOPPS!!! Job {job_id} failed: {str(e)}")

@router.post("/assign-async", status_code=status.HTTP_202_ACCEPTED)
async def assign_single_internship_async(
    request: InternshipIDRequest,
    background_tasks: BackgroundTasks
):
    job_id = str(uuid.uuid4())

    single_assignment_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "internship_id": str(request.internship_id),
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None
    }

    background_tasks.add_task(
        run_single_assignment_job,
        job_id,
        request.internship_id
    )
    return {
        "job_id": job_id,
        "status": "pending",
        "internship_id": str(request.internship_id),
        "message": "Assignment started in background",
        "check_status_url": f"/api/v1/assignments/single-job/{job_id}"
    }

@router.get("/single-job/{job_id}")
async def get_single_assignment_status(job_id: str):

    if job_id not in single_assignment_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = single_assignment_jobs[job_id]
    
    response = {
        "job_id": job["job_id"],
        "status": job["status"],
        "internship_id": job["internship_id"],
        "created_at": job["created_at"].isoformat() if job["created_at"] else None,
        "started_at": job["started_at"].isoformat() if job["started_at"] else None,
        "completed_at": job["completed_at"].isoformat() if job["completed_at"] else None,
    }

    if job["status"] == "completed" and job["result"]:
        result = job["result"]
        response["result"] = {
            "internship_id": result['internship_id'],
            "topic_id": result['topic_id'],
            "topic_number": result['topic_number'],
            "label": result['label'],
            "confidence": result.get('confidence'),
            "previous_topic_id": result.get('previous_topic_id'),
            "message": f"Successfully assigned to topic {result['topic_number']}: {result['label']}"
        }
    
    if job["status"] == "failed" and job["error"]:
        response["error"] = job["error"]
    
    return response

@router.post("/assign-batch-async", status_code=status.HTTP_202_ACCEPTED)
async def assign_batch_internships_async(
    request: InternshipIDsRequest,
    background_tasks: BackgroundTasks
):
    job_id = str(uuid.uuid4())
    
    batch_assignment_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "total": len(request.internship_ids),
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None
    }

    background_tasks.add_task(
        run_batch_assignment_job,
        job_id,
        request.internship_ids
    )
    return {
        "job_id": job_id,
        "status": "pending",
        "total": len(request.internship_ids),
        "message": "Batch assignment started in background",
        "check_status_url": f"/api/v1/assignments/job/{job_id}"
    }

@router.get("/job/{job_id}")
async def get_batch_assignment_status(job_id: str):
    
    if job_id not in batch_assignment_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_assignment_jobs[job_id]

    response = {
        "job_id": job["job_id"],
        "status": job["status"],
        "total": job["total"],
        "created_at": job["created_at"].isoformat() if job["created_at"] else None,
        "started_at": job["started_at"].isoformat() if job["started_at"] else None,
        "completed_at": job["completed_at"].isoformat() if job["completed_at"] else None,
    }
    
    if job["status"] == "completed" and job["result"]:
        result = job["result"]
        response["result"] = {
            "total": result['total'],
            "assigned": result['assigned'],
            "failed": result['failed'],
            "message": f"Assigned {result['assigned']} out of {result['total']} internships"
        }

    if job["status"] == "failed" and job["error"]:
        response["error"] = job["error"]
    
    return response

