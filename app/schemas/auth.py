from typing import List, Optional, ForwardRef, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.schemas.base import UserBase, DepartmentBase

Role = ForwardRef('Role')
Permission = ForwardRef('Permission')

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    department_code: Optional[str] = None
    roles: List[str] = []
    scopes: List[str] = []
    is_superuser: bool = False

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    is_active: Optional[bool] = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

# Import opinion schemas after base models
from app.schemas.opinion import (
    OpinionRequestInDB,
    DocumentInDB,
    RemarkInDB,
    RequestAssignmentInDB,
    OpinionInDB,
    WorkflowHistoryInDB,
    InterdepartmentalCommunicationBase
)

class User(UserBase):
    roles: List['Role'] = []
    department_id: Optional[int] = None
    department: Optional[DepartmentBase] = None
    
    # Opinion-related relationships
    opinion_requests: List[OpinionRequestInDB] = []
    deleted_opinions: List[OpinionRequestInDB] = []
    uploaded_documents: List[DocumentInDB] = []
    remarks: List[RemarkInDB] = []
    assigned_requests: List[RequestAssignmentInDB] = []
    expert_assignments: List[RequestAssignmentInDB] = []
    expert_opinions: List[OpinionInDB] = []
    reviewed_opinions: List[OpinionInDB] = []
    workflow_actions: List[WorkflowHistoryInDB] = []
    sent_communications: List[InterdepartmentalCommunicationBase] = []
    received_communications: List[InterdepartmentalCommunicationBase] = []

    class Config:
        from_attributes = True

# Role models
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: List[str] = []

class Role(RoleBase):
    id: int
    created_at: datetime
    permissions: List[Permission] = []

    class Config:
        from_attributes = True

# Permission models
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class Permission(PermissionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Login models
class LoginRequest(BaseModel):
    username: str
    password: str

# List models
class UserList(BaseModel):
    total: int
    items: List[User]
    
    class Config:
        from_attributes = True

# Password Change
class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# Response models
class UserResponse(BaseModel):
    success: bool
    message: str
    data: Optional[User] = None

# Search Parameters
class UserSearchParams(BaseModel):
    skip: int = 0
    limit: int = 100
    search: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[str] = None
    department_id: Optional[int] = None

# Extended Response Models
class UserDetail(User):
    total_opinions: int = 0
    total_assignments: int = 0
    recent_activities: List[Dict[str, Any]] = []

class UserStats(BaseModel):
    total_requests: int = 0
    total_opinions: int = 0
    total_reviews: int = 0
    pending_assignments: int = 0
    completed_assignments: int = 0

# Resolve forward references
User.model_rebuild()
Role.model_rebuild()
Permission.model_rebuild()