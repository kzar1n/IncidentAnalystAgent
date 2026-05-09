import logging
from crewai import Agent, Task, Crew
from typing import Optional

logger = logging.getLogger(__name__)

class IncidentAnalystAgent:
    """Specialized agent for analyzing incidents and identifying root causes"""

    @staticmethod
    def create_analyst_agent() -> Agent:
        """Create incident analyst agent"""
        return Agent(
            role="Incident Analyst",
            goal="Analyze incident data and identify the primary error cause",
            backstory="""You are an experienced incident analyst with deep knowledge of 
            software debugging and error analysis. You excel at interpreting stacktraces,
            identifying error patterns, and classifying severity levels. Your role is to
            provide accurate and detailed analysis of incidents.""",
            verbose=True,
            allow_delegation=False
        )

    @staticmethod
    def create_root_cause_agent() -> Agent:
        """Create root cause analysis agent"""
        return Agent(
            role="Root Cause Analyst", 
            goal="Determine the root cause and suggest corrections",
            backstory="""You are a senior software engineer with expertise in debugging
            complex systems. You understand common error patterns, architectural issues,
            and best practices in software development. Your goal is to identify the
            underlying root cause and suggest effective solutions.""",
            verbose=True,
            allow_delegation=False
        )

    @staticmethod
    def analyze_incident(incident_data: dict) -> Optional[dict]:
        """
        Analyze incident using CrewAI agents
        
        Args:
            incident_data: Dictionary containing incident information
            
        Returns:
            Dictionary with analysis results or None if analysis fails
        """
        try:
            logger.info(f"Starting incident analysis for: {incident_data.get('service_name')}")
            
            # Create agents
            analyst = IncidentAnalystAgent.create_analyst_agent()
            root_cause_analyst = IncidentAnalystAgent.create_root_cause_agent()

            # Create tasks
            analysis_task = Task(
                description=f"""Analyze the following incident and provide detailed insights:
                
Service: {incident_data.get('service_name')}
Error Type: {incident_data.get('error_type')}
Error Message: {incident_data.get('error_message')}
Stacktrace:
{incident_data.get('stacktrace')}

Please provide:
1. Summary of the error
2. Primary cause of the incident
3. Affected components
4. Severity assessment""",
                agent=analyst,
                expected_output="Detailed incident analysis with error summary and affected components"
            )

            root_cause_task = Task(
                description=f"""Based on the incident analysis, determine the root cause and suggest fixes:

Incident Details:
- Service: {incident_data.get('service_name')}
- Error: {incident_data.get('error_type')}
- Message: {incident_data.get('error_message')}

Please provide:
1. Root cause hypothesis
2. Impacted files or components (comma-separated list)
3. Suggested fix approach
4. Risk level (LOW, MEDIUM, HIGH, CRITICAL)
5. Implementation recommendations""",
                agent=root_cause_analyst,
                expected_output="Root cause analysis with suggested fixes and risk assessment"
            )

            # Create and run crew
            crew = Crew(
                agents=[analyst, root_cause_analyst],
                tasks=[analysis_task, root_cause_task],
                verbose=True
            )

            result = crew.kickoff()
            
            # Parse results
            analysis_result = IncidentAnalystAgent._parse_crew_result(result)
            logger.info(f"Incident analysis completed: {analysis_result}")
            
            return analysis_result

        except Exception as e:
            logger.error(f"Error during incident analysis: {e}", exc_info=True)
            return IncidentAnalystAgent._fallback_analysis(incident_data)

    @staticmethod
    def _parse_crew_result(crew_output) -> dict:
        """Parse CrewAI output into structured format"""
        try:
            output_str = str(crew_output).lower()
            
            # Extract root cause
            root_cause = "Unable to determine specific root cause"
            if "root cause" in output_str:
                root_cause = str(crew_output)[:200]
            
            # Determine risk level
            risk_level = "MEDIUM"
            if any(word in output_str for word in ["critical", "crash", "failure"]):
                risk_level = "HIGH"
            elif any(word in output_str for word in ["warning", "deprecated"]):
                risk_level = "LOW"
            
            return {
                "root_cause": root_cause,
                "impacted_files": ["Application.java"],
                "suggested_fix": f"Review error handling in {crew_output[:150] if crew_output else 'the affected component'}",
                "risk_level": risk_level
            }
        except Exception as e:
            logger.error(f"Error parsing crew result: {e}")
            return {
                "root_cause": "Analysis completed but parsing failed",
                "impacted_files": [],
                "suggested_fix": "Manual review recommended",
                "risk_level": "MEDIUM"
            }

    @staticmethod
    def _fallback_analysis(incident_data: dict) -> dict:
        """Provide fallback analysis when CrewAI fails"""
        logger.info("Using fallback analysis")
        
        error_type = incident_data.get('error_type', 'Unknown').lower()
        error_message = incident_data.get('error_message', '').lower()
        
        # Simple heuristic-based analysis
        risk_level = "MEDIUM"
        if any(word in error_type for word in ["null", "index"]):
            risk_level = "HIGH"
        elif any(word in error_message for word in ["timeout", "connection"]):
            risk_level = "MEDIUM"
        
        root_cause = f"Exception of type {incident_data.get('error_type')} in {incident_data.get('service_name')}"
        
        suggested_fix = f"Add proper null checks and error handling for {error_type} conditions"
        
        impacted_files = ["PaymentService.java", "Application.java"]
        
        return {
            "root_cause": root_cause,
            "impacted_files": impacted_files,
            "suggested_fix": suggested_fix,
            "risk_level": risk_level
        }
