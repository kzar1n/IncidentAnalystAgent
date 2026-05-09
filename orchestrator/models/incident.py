from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IncidentStatus(str, Enum):
    RECEIVED = "received"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    RESOLVED = "resolved"
    FAILED = "failed"

class IncidentBase(BaseModel):
    severity: SeverityLevel
    service_name: str
    error_type: str
    stacktrace: str
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class IncidentCreate(IncidentBase):
    pass

class Incident(IncidentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: IncidentStatus = IncidentStatus.RECEIVED
    root_cause: Optional[str] = None
    impacted_files: List[str] = Field(default_factory=list)
    suggested_fix: Optional[str] = None
    risk_level: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

class AnalysisResult(BaseModel):
    incident_id: str
    root_cause: str
    impacted_files: List[str]
    suggested_fix: str
    risk_level: str
    analysis_summary: str

class WebhookPayload(BaseModel):
    """Webhook payload from SigNoz"""
    alerts: Optional[List[dict]] = []
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    stacktrace: Optional[str] = None
    service_name: Optional[str] = None
    severity: Optional[str] = None
    timestamp: Optional[str] = None
