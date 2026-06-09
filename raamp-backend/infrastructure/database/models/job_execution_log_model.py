# Infrastructure Layer - Job Execution Log Model
from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Dict, Optional


class JobExecutionLogModel(Document):
    """Model to track job executions"""
    job_id: Indexed(str) = Field(..., description="Unique job identifier")
    execution_id: str = Field(..., description="Unique execution identifier")
    started_at: datetime = Field(default_factory=datetime.now, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    status: str = Field(default="RUNNING", description="RUNNING, COMPLETED, FAILED")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    result: Optional[Dict] = Field(None, description="Job result/output")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Settings:
        name = "job_execution_logs"
        indexes = [
            [("job_id", 1), ("started_at", -1)],
            [("status", 1)],
            [("started_at", -1)]
        ]
