from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from typing import  Dict, Any
import uuid
from datetime import datetime
import numpy as np

from app.internship.models.schemas import (
    ClusterAllRequest,
    ClusteringResult,
    TopicListResponse,
    TopicInfo,
    ErrorResponse
)
from app.internship.services.clustering import ClusteringService
from app.internship.services.vector_db import VectorDBService
from app.internship.core.database import get_db_connection
import pandas as pd

router = APIRouter( )

clustering_jobs: Dict[str, Dict[str, Any]] = {}

def convert_numpy_types(obj):
    """
    Recursively convert numpy types to Python native types for JSON serialization
    """
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

def run_clustering_job(job_id: str, topic_version: str, n_topics: str):
    try:
        # 1- update status to running
        clustering_jobs[job_id]["status"] = "running"
        clustering_jobs[job_id]["started_at"] = datetime.now()
        
        print(f"\n Starting clustering job {job_id}...")
        
        # 2- run clustering 
        clustering_service = ClusteringService()
        result = clustering_service.cluster_all_internships(
            topic_version=topic_version,
            n_topics=n_topics or "auto"
        )
        
        # 3- rebuild vector DB
        print(f"\n Rebuilding vector DB for job {job_id}...")
        vector_db = VectorDBService()
        vector_db.rebuild_from_database()
        
        # 4- using helper function for serializability
        result = convert_numpy_types(result)
        
        # 5- update job with success
        clustering_jobs[job_id].update({
            "status": "completed",
            "completed_at": datetime.now(),
            "result": result,
            "error": None
        })
        
        print(f"\n Job {job_id} completed successfully!")
        
    except Exception as e:
        # if there is an error, update job with error
        clustering_jobs[job_id].update({
            "status": "failed",
            "completed_at": datetime.now(),
            "error": str(e)
        })
        print(f"\nOPPS  Job {job_id} failed: {str(e)}")

@router.post("/cluster-all-async", status_code=status.HTTP_202_ACCEPTED)
async def cluster_all_internships_async(
    request: ClusterAllRequest,
    background_tasks: BackgroundTasks
):


    # 1- generate job ID
    job_id = str(uuid.uuid4())
    
    # 2- initialize job tracking
    clustering_jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "topic_version": request.topic_version,
        "n_topics": request.n_topics or "auto",
        "created_at": datetime.now(),
        "started_at": None,
        "completed_at": None,
        "result": None,
        "error": None
    }
    
    # 3- add to background tasks
    background_tasks.add_task(
        run_clustering_job,
        job_id,
        request.topic_version,
        request.n_topics or "auto"
    )
    
    # 4- return immediately
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Clustering started in background",
        "check_status_url": f"/api/v1/topics/job/{job_id}"
    }

@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    if job_id not in clustering_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = clustering_jobs[job_id]
    
    # response based on status 
    response = {
        "job_id": job["job_id"],
        "status": job["status"],
        "topic_version": job["topic_version"],
        "n_topics": job["n_topics"],
        "created_at": job["created_at"].isoformat() if job["created_at"] else None,
        "started_at": job["started_at"].isoformat() if job["started_at"] else None,
        "completed_at": job["completed_at"].isoformat() if job["completed_at"] else None,
    }
    
    # assign result if completed
    if job["status"] == "completed" and job["result"]:
        result = job["result"]
        response["result"] = {
            "topic_version": result['topic_version'],
            "n_topics": result['n_topics'],
            "silhouette_score": result['silhouette_score'],
            "total_internships": result['total_internships'],
            "message": f"Successfully clustered {result['total_internships']} internships into {result['n_topics']} topics"
        }
    
    # assign error if failed
    if job["status"] == "failed" and job["error"]:
        response["error"] = job["error"]
    
    return response


