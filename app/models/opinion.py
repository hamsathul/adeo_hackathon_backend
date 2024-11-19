#app/models/opinion.py
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime, Boolean, 
    JSON, CheckConstraint, Float, Index
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.auth import User
from app.models.department import Department

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
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("department.id"), nullable=False)

    priority = Column(String(20))
    current_status_id = Column(Integer, ForeignKey("workflow_status.id"))
    due_date = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sub_category_id = Column(Integer, ForeignKey("subcategories.id"))
    
    # New detailed fields
    request_statement = Column(Text)  # New
    challenges_opportunities = Column(Text)  # New
    subject_content = Column(Text)  # New
    alternative_options = Column(Text)  # New
    expected_impact = Column(Text)  # New
    potential_risks = Column(Text)  # New
    studies_statistics = Column(Text)  # New
    legal_financial_opinions = Column(Text)  # New
    stakeholder_feedback = Column(Text)  # New
    work_plan = Column(Text)  # New
    decision_draft = Column(Text)  # New
    version = Column(Integer, default=1)
    
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
        # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="opinion_requests")
    deleted_by_user = relationship("User", foreign_keys=[deleted_by], back_populates="deleted_opinions")
    department = relationship("Department", foreign_keys=[department_id], back_populates="opinion_requests")
    current_status = relationship("WorkflowStatus")
    assignments = relationship("RequestAssignment", back_populates="request")
    documents = relationship("Document", back_populates="request", cascade="all, delete-orphan", order_by="Document.created_at.desc()")
    remarks = relationship("Remark", back_populates="request", cascade="all, delete-orphan", order_by="Remark.created_at.desc()")
    opinions = relationship("Opinion", back_populates="request", cascade="all, delete-orphan")
    category_rel = relationship("Category", foreign_keys=[category_id])  # Need to update
    subcategory_rel = relationship("SubCategory", foreign_keys=[sub_category_id])
    workflow_history = relationship("WorkflowHistory", back_populates="request", cascade="all, delete-orphan")
    communications = relationship("InterdepartmentalCommunication", back_populates="request", cascade="all, delete-orphan")  

    # Update priority constraint
    __table_args__ = (
        CheckConstraint(
            priority.in_(['urgent', 'high', 'medium', 'low']),  # Updated to match React component
            name='valid_priority'
        ),
    )



class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True)
    opinion_request_id = Column(Integer, ForeignKey("opinion_requests.id"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(255))
    file_size = Column(Integer)
    file_url = Column(String(512))  # New - for storing URLs
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())
    
    request = relationship("OpinionRequest", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
    
class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())
    
    opinion_requests = relationship("OpinionRequest", back_populates="category_rel")
    subcategories = relationship("SubCategory", back_populates="category")

class SubCategory(Base):
    __tablename__ = "subcategories"
    
    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    category = relationship("Category", back_populates="subcategories")
    opinion_requests = relationship("OpinionRequest", back_populates="subcategory_rel")
    
    __table_args__ = (
        Index('idx_subcategory_category', category_id, name, unique=True),
    )
    
class Remark(Base):
    __tablename__ = "remarks"
    
    id = Column(Integer, primary_key=True)
    opinion_request_id = Column(Integer, ForeignKey("opinion_requests.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    request = relationship("OpinionRequest", back_populates="remarks")
    user = relationship("User", back_populates="remarks")

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
    assigner = relationship("User", foreign_keys=[assigned_by], back_populates="assigned_requests")
    expert = relationship("User", foreign_keys=[expert_id], back_populates="expert_assignments")
    status = relationship("WorkflowStatus")
    
    __table_args__ = (
        Index('uix_request_expert', opinion_request_id, expert_id, unique=True),
    )

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
    department = relationship("Department", back_populates="opinions")
    expert = relationship("User", foreign_keys=[expert_id], back_populates="expert_opinions")
    reviewer = relationship("User", foreign_keys=[reviewed_by], back_populates="reviewed_opinions")

    __table_args__ = (
        CheckConstraint(
            status.in_(['draft', 'submitted', 'reviewed', 'approved', 'rejected', 'unassigned']),
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

    request = relationship("OpinionRequest", back_populates="communications")
    comm_type = relationship("CommunicationType")
    from_department = relationship("Department", foreign_keys=[from_department_id])
    to_department = relationship("Department", foreign_keys=[to_department_id])
    from_user = relationship("User", foreign_keys=[from_user_id], back_populates="sent_communications")
    to_user = relationship("User", foreign_keys=[to_user_id], back_populates="received_communications")
    parent_communication = relationship("InterdepartmentalCommunication", remote_side=[id])
    
    __table_args__ = (
        CheckConstraint(
            priority.in_(['urgent', 'high', 'medium', 'low']),
            name='valid_comm_priority'
        ),
        CheckConstraint(
            status.in_(['pending', 'in_progress', 'completed', 'cancelled']),
            name='valid_comm_status'
        ),
        CheckConstraint(
            to_department_id != from_department_id,
            name='different_departments'
        )
    )

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
    
    request = relationship("OpinionRequest", back_populates="workflow_history")
    actor = relationship("User", back_populates="workflow_actions")
    from_status = relationship("WorkflowStatus", foreign_keys=[from_status_id])
    to_status = relationship("WorkflowStatus", foreign_keys=[to_status_id])

# Create indexes
Index('idx_opinion_requests_status', OpinionRequest.current_status_id)
Index('idx_opinion_requests_department', OpinionRequest.department_id)
Index('idx_opinions_request', Opinion.opinion_request_id)
Index('idx_workflow_history_request', WorkflowHistory.opinion_request_id)
Index('idx_opinion_requests_category_id', OpinionRequest.category_id)
Index('idx_opinion_requests_subcategory_id', OpinionRequest.sub_category_id)
Index('idx_remarks_request', Remark.opinion_request_id)
Index('idx_documents_request', Document.opinion_request_id)
Index('idx_assignments_request', RequestAssignment.opinion_request_id)
Index('idx_communications_request', InterdepartmentalCommunication.opinion_request_id)