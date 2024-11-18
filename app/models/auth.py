# app/models/auth.py
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

# Association Tables for Many-to-Many Relationships
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'))
)

role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE')),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'))
)

class User(Base):
    __tablename__ = "users"  # Changed from 'user' to 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    department_id = Column(Integer, ForeignKey('department.id'), nullable=True)    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    department = relationship("Department", back_populates="users")
    chat_messages = relationship("ChatMessage", back_populates="user")
    opinion_requests = relationship("OpinionRequest", foreign_keys="OpinionRequest.requester_id", back_populates="requester")
    deleted_opinions = relationship("OpinionRequest", foreign_keys="OpinionRequest.deleted_by", back_populates="deleted_by_user")
    
    # Document relationship
    uploaded_documents = relationship("Document", back_populates="uploader")
    
    # Remark relationship
    remarks = relationship("Remark", back_populates="user")
    
    # RequestAssignment relationships
    assigned_requests = relationship("RequestAssignment", 
                                   foreign_keys="RequestAssignment.assigned_by", 
                                   back_populates="assigner")
    expert_assignments = relationship("RequestAssignment", 
                                    foreign_keys="RequestAssignment.expert_id", 
                                    back_populates="expert")
    
    # Opinion relationships
    expert_opinions = relationship("Opinion",
                                 foreign_keys="Opinion.expert_id",
                                 back_populates="expert")
    reviewed_opinions = relationship("Opinion",
                                   foreign_keys="Opinion.reviewed_by",
                                   back_populates="reviewer")
    
    # WorkflowHistory relationship
    workflow_actions = relationship("WorkflowHistory",
                                  foreign_keys="WorkflowHistory.action_by",
                                  back_populates="actor")
    
    # Communication relationships
    sent_communications = relationship("InterdepartmentalCommunication",
                                     foreign_keys="InterdepartmentalCommunication.from_user_id",
                                     back_populates="from_user")
    received_communications = relationship("InterdepartmentalCommunication",
                                         foreign_keys="InterdepartmentalCommunication.to_user_id",
                                         back_populates="to_user")

class Role(Base):
    __tablename__ = "roles"  # Changed from 'role' to 'roles'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"  # Changed from 'permission' to 'permissions'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")