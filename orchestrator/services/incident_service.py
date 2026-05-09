import logging
import uuid
from datetime import datetime
from typing import Optional, Dict
from models.incident import Incident, IncidentCreate, SeverityLevel, IncidentStatus
from services.database import Database
from services.signoz_parser import SigNozParser
from agents.incident_analyst import IncidentAnalystAgent

logger = logging.getLogger(__name__)

class IncidentService:
    """Service for managing incident creation and analysis"""

    def __init__(self, db: Database):
        self.db = db

    async def process_webhook(self, webhook_payload: dict) -> Optional[Dict]:
        """
        Process webhook from SigNoz and create incident
        
        Args:
            webhook_payload: Raw webhook payload from SigNoz
            
        Returns:
            Analysis result dictionary or None if processing fails
        """
        try:
            logger.info("Processing webhook payload")
            
            # Parse webhook payload
            incident_data = SigNozParser.parse_webhook(webhook_payload)
            
            if not incident_data:
                logger.warning("Failed to parse webhook payload")
                return None
            
            # Create incident in database
            incident_id = await self.create_incident(incident_data)
            
            if not incident_id:
                logger.error("Failed to create incident")
                return None
            
            # Analyze incident with AI agents
            analysis_result = await self.analyze_incident_with_ai(incident_id, incident_data)
            
            if analysis_result:
                # Update incident with analysis results
                await self.update_incident_analysis(incident_id, analysis_result)
                logger.info(f"Incident {incident_id} analysis completed successfully")
                return analysis_result
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return None

    async def create_incident(self, incident_data: dict) -> Optional[str]:
        """
        Create new incident in database
        
        Args:
            incident_data: Incident data dictionary
            
        Returns:
            Incident ID or None if creation fails
        """
        try:
            incident_id = str(uuid.uuid4())
            incident_record = {
                'id': incident_id,
                'timestamp': incident_data.get('timestamp', datetime.utcnow()),
                'severity': incident_data.get('severity', 'high'),
                'service_name': incident_data.get('service_name', 'unknown'),
                'error_type': incident_data.get('error_type', 'Unknown'),
                'error_message': incident_data.get('error_message', ''),
                'stacktrace': incident_data.get('stacktrace', ''),
            }
            
            returned_id = self.db.create_incident(incident_record)
            logger.info(f"Incident created with ID: {returned_id}")
            return returned_id
            
        except Exception as e:
            logger.error(f"Error creating incident: {e}", exc_info=True)
            return None

    async def analyze_incident_with_ai(self, incident_id: str, incident_data: dict) -> Optional[Dict]:
        """
        Analyze incident using CrewAI agents
        
        Args:
            incident_id: ID of the incident
            incident_data: Incident data
            
        Returns:
            Analysis result dictionary or None if analysis fails
        """
        try:
            logger.info(f"Starting AI analysis for incident {incident_id}")
            
            # Use CrewAI agents for analysis
            analysis_result = IncidentAnalystAgent.analyze_incident(incident_data)
            
            if analysis_result:
                analysis_result['incident_id'] = incident_id
                logger.info(f"AI analysis completed for incident {incident_id}")
                return analysis_result
            
            logger.warning(f"AI analysis failed for incident {incident_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error during AI analysis: {e}", exc_info=True)
            return None

    async def update_incident_analysis(self, incident_id: str, analysis_result: dict) -> bool:
        """
        Update incident with analysis results
        
        Args:
            incident_id: ID of the incident
            analysis_result: Analysis result dictionary
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            update_data = {
                'root_cause': analysis_result.get('root_cause'),
                'impacted_files': analysis_result.get('impacted_files', []),
                'suggested_fix': analysis_result.get('suggested_fix'),
                'risk_level': analysis_result.get('risk_level'),
            }
            
            success = self.db.update_incident_analysis(incident_id, update_data)
            
            if success:
                logger.info(f"Incident {incident_id} analysis results persisted")
            else:
                logger.warning(f"Failed to update incident {incident_id} analysis")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating incident analysis: {e}", exc_info=True)
            return False

    def get_incident(self, incident_id: str) -> Optional[Dict]:
        """Get incident by ID"""
        try:
            return self.db.get_incident(incident_id)
        except Exception as e:
            logger.error(f"Error getting incident: {e}", exc_info=True)
            return None

    def list_incidents(self, limit: int = 50, offset: int = 0) -> list:
        """List incidents"""
        try:
            return self.db.list_incidents(limit, offset)
        except Exception as e:
            logger.error(f"Error listing incidents: {e}", exc_info=True)
            return []
