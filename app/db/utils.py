# app/db/utils.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any

def check_database_connection(db: Session) -> Dict[str, Any]:
    """Test database connection with more details"""
    try:
        # Test basic connection
        version = db.execute(text("SELECT version()")).scalar()
        
        # Get database statistics
        stats = db.execute(
            text("""
                SELECT 
                    numbackends as active_connections,
                    xact_commit as transactions_committed,
                    blks_read as blocks_read,
                    blks_hit as blocks_hit
                FROM pg_stat_database 
                WHERE datname = current_database()
            """)
        ).first()

        return {
            "status": "success",
            "database_version": version,
            "statistics": {
                "active_connections": stats[0] if stats else None,
                "transactions_committed": stats[1] if stats else None,
                "blocks_read": stats[2] if stats else None,
                "blocks_hit": stats[3] if stats else None
            }
        }
    except SQLAlchemyError as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }