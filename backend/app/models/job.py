from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime

JobStatus = Literal["pending", "running", "success", "error"]


class JobState(BaseModel):
    """Persisted job state"""
    job_id: str
    status: JobStatus
    pid: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DriverJobResponse(BaseModel):
    """Response when starting driver job"""
    job_id: str


class DriverStatusResponse(BaseModel):
    """Current status of a driver job"""
    job_id: str
    status: JobStatus
    cart_count: int = 0
    knot_api_count: int = 0
    message: Optional[str] = None

