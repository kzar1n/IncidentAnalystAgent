import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, List
from models.incident import WebhookPayload, AnalysisResult
from services.incident_service import IncidentService
from services.database import Database

logger = logging.getLogger(__name__)

db = Database()
incident_service = IncidentService(db)

router = APIRouter()

@router.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        db.connect()
        db.initialize_schema()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

@router.on_event("shutdown")
async def shutdown_event():
    """Close database on shutdown"""
    db.close()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "UP",
        "service": "incident-orchestrator"
    }

@router.post("/incidents")
async def create_incident_from_webhook(
    payload: WebhookPayload,
    background_tasks: BackgroundTasks
):
    """
    Receive webhook from SigNoz and trigger incident analysis
    
    Args:
        payload: Webhook payload from SigNoz
        background_tasks: FastAPI background tasks for async processing
        
    Returns:
        Initial response with incident receipt confirmation
    """
    try:
        logger.info("Received webhook payload", extra={"payload": payload})
        
        # Convert to dict for processing
        payload_dict = payload.model_dump()
        
        # Process webhook asynchronously
        background_tasks.add_task(incident_service.process_webhook, payload_dict)
        
        return {
            "status": "received",
            "message": "Incident received and queued for analysis"
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process webhook")

@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """
    Retrieve incident by ID
    
    Args:
        incident_id: UUID of the incident
        
    Returns:
        Incident details or 404 if not found
    """
    try:
        incident = incident_service.get_incident(incident_id)
        
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return incident
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve incident")

@router.get("/incidents")
async def list_incidents(limit: int = 50, offset: int = 0):
    """
    List incidents with pagination
    
    Args:
        limit: Number of incidents to return (max 50)
        offset: Number of incidents to skip
        
    Returns:
        List of incidents
    """
    try:
        limit = min(limit, 50)  # Cap limit at 50
        incidents = incident_service.list_incidents(limit, offset)
        
        return {
            "incidents": incidents,
            "count": len(incidents),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing incidents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list incidents")

@router.post("/incidents/analyze")
async def analyze_incident_manual(
    service_name: str,
    error_type: str,
    error_message: str,
    stacktrace: str,
    severity: str = "high"
):
    """
    Manually trigger incident analysis
    
    Useful for testing without SigNoz webhook
    
    Args:
        service_name: Name of the service
        error_type: Type of error
        error_message: Error message
        stacktrace: Error stacktrace
        severity: Severity level
        
    Returns:
        Analysis result
    """
    try:
        incident_data = {
            'service_name': service_name,
            'error_type': error_type,
            'error_message': error_message,
            'stacktrace': stacktrace,
            'severity': severity,
        }
        
        # Process incident
        analysis_result = await incident_service.process_webhook(incident_data)
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="Analysis failed")
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing incident: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze incident")
