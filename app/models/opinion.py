#app/models/opinion.py
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Boolean, 
    JSON, CheckConstraint, Float, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class WorkflowStatus(Base):
    __tablename__ = "workflow_status"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

class OpinionRequest(Base):
    __tablename__ = "opinion_requests"
    
    id = Column(Integer, primary_key=True)
    reference_number = Column(String(50), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"))
    department_id = Column(Integer, ForeignKey("department.id"))
    priority = Column(String(20))
    current_status_id = Column(Integer, ForeignKey("workflow_status.id"))
    due_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    department = relationship("Department", foreign_keys=[department_id])
    current_status = relationship("WorkflowStatus")
    documents = relationship("Document", back_populates="request")
    assignments = relationship("RequestAssignment", back_populates="request")
    opinions = relationship("Opinion", back_populates="request")

    __table_args__ = (
        CheckConstraint(
            priority.in_(['Low', 'Medium', 'High', 'Urgent']),
            name='valid_priority'
        ),
    )

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    opinion_request_id = Column(Integer, ForeignKey("opinion_requests.id"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    request = relationship("OpinionRequest", back_populates="documents")
    uploader = relationship("User")

class RequestAssignment(Base):
    __tablename__ = "request_assignments"
    
    id = Column(Integer, primary_key=True)
    opinion_request_id = Column(Integer, ForeignKey("opinion_requests.id"))
    department_id = Column(Integer, ForeignKey("department.id"))
    assigned_by = Column(Integer, ForeignKey("users.id"))
    expert_id = Column(Integer, ForeignKey("users.id"))
    status_id = Column(Integer, ForeignKey("workflow_status.id"))
    assigned_at = Column(DateTime, server_default=func.now())
    due_date = Column(DateTime)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    request = relationship("OpinionRequest", back_populates="assignments")
    department = relationship("Department")
    assigner = relationship("User", foreign_keys=[assigned_by])
    expert = relationship("User", foreign_keys=[expert_id])
    status = relationship("WorkflowStatus")

class Opinion(Base):
    __tablename__ = "opinions"
    
    id = Column(Integer, primary_key=True)
    opinion_request_id = Column(Integer, ForeignKey("opinion_requests.id"))
    department_id = Column(Integer, ForeignKey("department.id"))
    expert_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    recommendation = Column(Text)
    status = Column(String(50), default='draft')
    review_comments = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    request = relationship("OpinionRequest", back_populates="opinions")
    department = relationship("Department")
    expert = relationship("User", foreign_keys=[expert_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        CheckConstraint(
            status.in_(['draft', 'submitted', 'reviewed', 'approved', 'rejected']),
            name='valid_status'
        ),
    )

class CommunicationType(Base):
    __tablename__ = "communication_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    requires_response = Column(Boolean, default=False)
    default_deadline_hours = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

class InterdepartmentalCommunication(Base):
    __tablename__ = "interdepartmental_communications"
    
    id = Column(Integer, primary_key=True)
    opinion_request_id = Column(Integer, ForeignKey("opinion_requests.id"))
    communication_type_id = Column(Integer, ForeignKey("communication_types.id"))
    from_department_id = Column(Integer, ForeignKey("department.id"))
    to_department_id = Column(Integer, ForeignKey("department.id"))
    from_user_id = Column(Integer, ForeignKey("users.id"))
    to_user_id = Column(Integer, ForeignKey("users.id"))
    subject = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(String(20), default='medium')
    status = Column(String(50), default='pending')
    due_date = Column(DateTime)
    parent_communication_id = Column(Integer, ForeignKey("interdepartmental_communications.id"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    request = relationship("OpinionRequest")
    comm_type = relationship("CommunicationType")
    from_department = relationship("Department", foreign_keys=[from_department_id])
    to_department = relationship("Department", foreign_keys=[to_department_id])
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])
    parent_communication = relationship("InterdepartmentalCommunication", remote_side=[id])

class WorkflowHistory(Base):
    __tablename__ = "workflow_history"
    
    id = Column(Integer, primary_key=True)
    opinion_request_id = Column(Integer, ForeignKey("opinion_requests.id"))
    action_type = Column(String(50), nullable=False)
    action_by = Column(Integer, ForeignKey("users.id"))
    from_status_id = Column(Integer, ForeignKey("workflow_status.id"))
    to_status_id = Column(Integer, ForeignKey("workflow_status.id"))
    action_details = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    
    request = relationship("OpinionRequest")
    actor = relationship("User")
    from_status = relationship("WorkflowStatus", foreign_keys=[from_status_id])
    to_status = relationship("WorkflowStatus", foreign_keys=[to_status_id])

# Create indexes
Index('idx_opinion_requests_status', OpinionRequest.current_status_id)
Index('idx_opinion_requests_department', OpinionRequest.department_id)
Index('idx_opinions_request', Opinion.opinion_request_id)
Index('idx_workflow_history_request', WorkflowHistory.opinion_request_id)