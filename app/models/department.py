from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class Department(Base):
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with users
    users = relationship("User", back_populates="department")
    
        # Opinion relationships
    opinion_requests = relationship("OpinionRequest", back_populates="department")
    opinions = relationship("Opinion", back_populates="department")