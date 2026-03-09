from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class SyncCandidateRequest(BaseModel):
    candidate_id: str = Field(..., description="candidate ID")


class SyncInternshipRequest(BaseModel):
    internship_id: str = Field(..., description="internship ID ")


class SearchInternshipsRequest(BaseModel):
    query: str = Field(..., description="search query", min_length=1)
    top_k: int = Field(20, ge=1, le=100, description="number of results to return")

