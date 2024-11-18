#app/schemas/opinion.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

class PriorityEnum(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    urgent = "Urgent"

class OpinionStatusEnum(str, Enum):
    draft = "draft"
    submitted = "submitted"
    reviewed = "reviewed"
    approved = "approved"
    rejected = "rejected"

# Base Schemas
class WorkflowStatusBase(BaseModel):
    name: str
    description: Optional[str] = None

class OpinionRequestBase(BaseModel):
    title: str
    description: str
    priority: PriorityEnum
    due_date: Optional[datetime] = None

class DocumentBase(BaseModel):
    file_name: str
    file_type: Optional[str] = None

class OpinionBase(BaseModel):
    content: str
    recommendation: Optional[str] = None

# Create Schemas
class OpinionRequestCreate(OpinionRequestBase):
    department_id: int

class DocumentCreate(DocumentBase):
    opinion_request_id: int

class OpinionCreate(OpinionBase):
    opinion_request_id: int
    department_id: int

# Update Schemas
class OpinionRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    due_date: Optional[datetime] = None

class OpinionUpdate(BaseModel):
    content: Optional[str] = None
    recommendation: Optional[str] = None
    status: Optional[OpinionStatusEnum] = None
    review_comments: Optional[str] = None

# Response Schemas
class WorkflowStatusInDB(WorkflowStatusBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class DocumentInDB(DocumentBase):
    id: int
    opinion_request_id: int
    file_path: str
    file_size: Optional[int]
    uploaded_by: int
    created_at: datetime

    class Config:
        orm_mode = True

class OpinionInDB(OpinionBase):
    id: int
    opinion_request_id: int
    department_id: int
    expert_id: int
    status: OpinionStatusEnum
    review_comments: Optional[str]
    reviewed_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class OpinionRequestInDB(OpinionRequestBase):
    id: int
    reference_number: str
    requester_id: int
    current_status_id: int
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentInDB]
    opinions: List[OpinionInDB]

    class Config:
        orm_mode = True

# Additional Schemas for specific operations
class OpinionRequestWithDetails(OpinionRequestInDB):
    current_status: WorkflowStatusInDB
    department: Dict[str, Any]  # Using existing department schema
    requester: Dict[str, Any]   # Using existing user schema

class OpinionReview(BaseModel):
    is_approved: bool
    comments: Optional[str] = None