import os
import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api.routes import router

# Configure JSON logging
def setup_logging():
    """Configure JSON logging for structured logs"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler()
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s %(trace_id)s %(span_id)s'
    )
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    return logger

# Setup logging
logger = setup_logging()

# Create FastAPI application
app = FastAPI(
    title="AI Incident Orchestrator",
    description="AI-Assisted Incident Resolution Platform - Orchestrator",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "incident-orchestrator",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/docs")
async def get_docs():
    """API documentation"""
    return JSONResponse({
        "title": "AI Incident Orchestrator API",
        "endpoints": [
            {
                "method": "GET",
                "path": "/health",
                "description": "Health check"
            },
            {
                "method": "POST",
                "path": "/incidents",
                "description": "Receive webhook from SigNoz"
            },
            {
                "method": "GET",
                "path": "/incidents",
                "description": "List incidents"
            },
            {
                "method": "GET",
                "path": "/incidents/{incident_id}",
                "description": "Get incident details"
            },
            {
                "method": "POST",
                "path": "/incidents/analyze",
                "description": "Manual incident analysis"
            }
        ]
    })

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting orchestrator on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=None  # Use our JSON logging
    )
