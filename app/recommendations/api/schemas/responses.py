from pydantic import BaseModel, Field
from typing import Optional, List

class SyncResponse(BaseModel):
    success: bool
    message: str
    candidate_id: Optional[str] = None
    internship_id: Optional[str] = None
    vector_id: Optional[str] = None
    timestamp: Optional[str] = None

class InternshipSearchResult(BaseModel):
    internship_id: str
    similarity_score: float

class SearchInternshipsResponse(BaseModel):
    query: str
    total_results: int
    results: List[InternshipSearchResult]

class InternshipIDsResponse(BaseModel):
    candidate_id: str
    total: int
    ids: List[str]

class CandidateIDsResponse(BaseModel):
    internship_id: str
    total: int
    ids: List[str]