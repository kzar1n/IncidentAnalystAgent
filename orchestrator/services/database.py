import os
import logging
from datetime import datetime
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import json

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.connection_string = (
            f"postgresql://{os.getenv('DB_USER', 'incident_user')}:"
            f"{os.getenv('DB_PASSWORD', 'incident_pass')}@"
            f"{os.getenv('DB_HOST', 'postgres')}:"
            f"{os.getenv('DB_PORT', '5432')}/"
            f"{os.getenv('DB_NAME', 'incident_db')}"
        )
        self.conn = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.connection_string)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def initialize_schema(self):
        """Initialize database schema"""
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS incidents (
                        id UUID PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        severity VARCHAR(50) NOT NULL,
                        service_name VARCHAR(255) NOT NULL,
                        error_type VARCHAR(255),
                        error_message TEXT,
                        stacktrace TEXT,
                        root_cause TEXT,
                        impacted_files TEXT[],
                        suggested_fix TEXT,
                        risk_level VARCHAR(50),
                        status VARCHAR(50) NOT NULL DEFAULT 'received',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    CREATE INDEX IF NOT EXISTS idx_incidents_timestamp 
                    ON incidents(timestamp DESC);
                    
                    CREATE INDEX IF NOT EXISTS idx_incidents_status 
                    ON incidents(status);
                    
                    CREATE INDEX IF NOT EXISTS idx_incidents_service 
                    ON incidents(service_name);
                """)
                self.conn.commit()
                logger.info("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize schema: {e}")
            self.conn.rollback()
            raise

    def create_incident(self, incident_data: dict) -> str:
        """Create a new incident"""
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO incidents 
                    (id, timestamp, severity, service_name, error_type, 
                     error_message, stacktrace, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    incident_data.get('id'),
                    incident_data.get('timestamp'),
                    incident_data.get('severity'),
                    incident_data.get('service_name'),
                    incident_data.get('error_type'),
                    incident_data.get('error_message'),
                    incident_data.get('stacktrace'),
                    'received'
                ))
                self.conn.commit()
                incident_id = cur.fetchone()[0]
                logger.info(f"Incident created: {incident_id}")
                return str(incident_id)
        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            self.conn.rollback()
            raise

    def update_incident_analysis(self, incident_id: str, analysis_data: dict) -> bool:
        """Update incident with analysis results"""
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE incidents
                    SET root_cause = %s,
                        impacted_files = %s,
                        suggested_fix = %s,
                        risk_level = %s,
                        status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s;
                """, (
                    analysis_data.get('root_cause'),
                    analysis_data.get('impacted_files'),
                    analysis_data.get('suggested_fix'),
                    analysis_data.get('risk_level'),
                    'analyzed',
                    incident_id
                ))
                self.conn.commit()
                logger.info(f"Incident {incident_id} updated with analysis")
                return True
        except Exception as e:
            logger.error(f"Failed to update incident: {e}")
            self.conn.rollback()
            return False

    def get_incident(self, incident_id: str) -> Optional[dict]:
        """Retrieve incident by ID"""
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM incidents WHERE id = %s;
                """, (incident_id,))
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get incident: {e}")
            return None

    def list_incidents(self, limit: int = 50, offset: int = 0) -> List[dict]:
        """List incidents with pagination"""
        if not self.conn:
            self.connect()

        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM incidents
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s;
                """, (limit, offset))
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to list incidents: {e}")
            return []
