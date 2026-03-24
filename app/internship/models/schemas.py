from pydantic import BaseModel, Field, UUID4
from typing import List, Optional
from datetime import datetime

class InternshipIDRequest(BaseModel):
    internship_id: UUID4 = Field(..., description="internship unique identifier")

class InternshipIDsRequest(BaseModel):
    internship_ids: List[UUID4] = Field(..., description="List of internship IDs", min_items=1)

class ClusterAllRequest(BaseModel):
    topic_version: Optional[str] = Field(None)  
    n_topics: Optional[str] = Field("auto")    

class TopicInfo(BaseModel):
    topic_id: UUID4
    topic_number: int
    label: str
    keywords: Optional[List[str]] = None
    description: Optional[str] = None
    document_count: Optional[int] = None
    silhouette_score: Optional[float] = None
    IsActive : bool
    created_at: datetime

class AssignmentResult(BaseModel):
    internship_id: UUID4
    topic_id: UUID4
    topic_number: int
    label: str
    confidence: Optional[float] = None
    previous_topic_id: Optional[UUID4] = None

class BatchAssignmentResponse(BaseModel):
    total: int
    assigned: int
    failed: int
    results: List[AssignmentResult]

class ClusteringResult(BaseModel):
    topic_version: str
    n_topics: int
    silhouette_score: float
    total_internships: int
    topics_created: List[TopicInfo]
    message: str

class TopicListResponse(BaseModel):
    total: int
    topics: List[TopicInfo]


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None