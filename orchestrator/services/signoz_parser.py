import logging
import json
from datetime import datetime
from typing import Optional, Dict
from models.incident import IncidentCreate, SeverityLevel

logger = logging.getLogger(__name__)

class SigNozParser:
    """Parser for SigNoz webhook payloads"""

    @staticmethod
    def parse_webhook(payload: dict) -> Optional[dict]:
        """
        Parse SigNoz webhook payload and extract incident information
        
        SigNoz sends alerts in various formats depending on the alert type.
        This parser handles different alert types and extracts the necessary information.
        """
        try:
            # Extract alerts from the payload
            alerts = payload.get('alerts', [])
            
            if not alerts:
                logger.warning("No alerts found in webhook payload")
                return None

            # Parse the first alert (primary concern)
            alert = alerts[0] if isinstance(alerts, list) else alerts
            
            # Extract common fields
            incident_data = {
                'severity': SigNozParser._extract_severity(alert),
                'service_name': SigNozParser._extract_service_name(alert, payload),
                'error_type': SigNozParser._extract_error_type(alert, payload),
                'error_message': SigNozParser._extract_error_message(alert, payload),
                'stacktrace': SigNozParser._extract_stacktrace(alert, payload),
                'timestamp': SigNozParser._extract_timestamp(alert, payload),
            }

            logger.info(f"Parsed incident: service={incident_data['service_name']}, "
                       f"error={incident_data['error_type']}")
            
            return incident_data

        except Exception as e:
            logger.error(f"Error parsing SigNoz webhook: {e}", exc_info=True)
            return None

    @staticmethod
    def _extract_severity(alert: dict) -> str:
        """Extract severity level from alert"""
        severity_mapping = {
            'critical': 'critical',
            'error': 'high',
            'warning': 'medium',
            'info': 'low',
            'debug': 'info'
        }
        
        # Try different alert field names
        severity_value = (
            alert.get('severity', '')
            or alert.get('level', '')
            or alert.get('alert_level', '')
            or 'high'
        ).lower()
        
        return severity_mapping.get(severity_value, 'high')

    @staticmethod
    def _extract_service_name(alert: dict, payload: dict) -> str:
        """Extract service name from alert"""
        return (
            alert.get('service_name')
            or alert.get('service')
            or alert.get('application_name')
            or payload.get('service_name')
            or payload.get('service')
            or 'unknown-service'
        )

    @staticmethod
    def _extract_error_type(alert: dict, payload: dict) -> str:
        """Extract error type from alert"""
        error_type = (
            alert.get('error_type')
            or alert.get('exception_type')
            or alert.get('metric_name')
            or payload.get('error_type')
            or payload.get('exception_type')
            or 'Exception'
        )
        
        # Clean up error type (remove package names if present)
        if '.' in str(error_type):
            error_type = str(error_type).split('.')[-1]
            
        return str(error_type)

    @staticmethod
    def _extract_error_message(alert: dict, payload: dict) -> str:
        """Extract error message from alert"""
        message = (
            alert.get('error_message')
            or alert.get('message')
            or alert.get('alert_message')
            or payload.get('error_message')
            or payload.get('message')
            or 'No error message provided'
        )
        
        return str(message)[:500]  # Limit message length

    @staticmethod
    def _extract_stacktrace(alert: dict, payload: dict) -> str:
        """Extract stacktrace from alert"""
        stacktrace = (
            alert.get('stacktrace')
            or alert.get('stack_trace')
            or alert.get('exception_stacktrace')
            or payload.get('stacktrace')
            or payload.get('stack_trace')
            or alert.get('error_message')
            or 'No stacktrace available'
        )
        
        if isinstance(stacktrace, list):
            stacktrace = '\n'.join(str(s) for s in stacktrace)
            
        return str(stacktrace)[:2000]  # Limit stacktrace length

    @staticmethod
    def _extract_timestamp(alert: dict, payload: dict) -> datetime:
        """Extract timestamp from alert"""
        timestamp_str = (
            alert.get('timestamp')
            or alert.get('alert_time')
            or payload.get('timestamp')
            or None
        )
        
        if timestamp_str:
            try:
                # Try parsing ISO format
                if isinstance(timestamp_str, str):
                    return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.warning(f"Failed to parse timestamp: {e}")
        
        return datetime.utcnow()
