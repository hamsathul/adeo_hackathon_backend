#app/schemas/opinion.py
from pydantic import BaseModel, Field
from fastapi import Form
from datetime import datetime
from typing import Optional, List, Dict, Any, ForwardRef
from enum import Enum
from app.schemas.base import UserBase, DepartmentBase

User = UserBase
Department = DepartmentBase
OpinionRequestInDB = ForwardRef('OpinionRequestInDB')
WorkflowStatusInDB = ForwardRef('WorkflowStatusInDB')

class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"

class OpinionStatusEnum(str, Enum):
    draft = "draft"
    submitted = "submitted"
    reviewed = "reviewed"
    approved = "approved"
    rejected = "rejected"
    unassigned = "unassigned"

class CommunicationStatusEnum(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

# Base Schemas
class WorkflowStatusBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryBase(BaseModel):
    name: str

class SubCategoryBase(BaseModel):
    name: str
    category_id: int

class OpinionRequestBase(BaseModel):
    title: str
    description: str
    priority: PriorityEnum
    due_date: Optional[datetime] = None
    category_id: int
    sub_category_id: Optional[int] = None
    request_statement: Optional[str] = None
    challenges_opportunities: Optional[str] = None
    subject_content: Optional[str] = None
    alternative_options: Optional[str] = None
    expected_impact: Optional[str] = None
    potential_risks: Optional[str] = None
    studies_statistics: Optional[str] = None
    legal_financial_opinions: Optional[str] = None
    stakeholder_feedback: Optional[str] = None
    work_plan: Optional[str] = None
    decision_draft: Optional[str] = None

class DocumentBase(BaseModel):
    file_name: str
    file_path: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_url: Optional[str] = None

class RemarkBase(BaseModel):
    content: str

class OpinionBase(BaseModel):
    content: str
    recommendation: Optional[str] = None

class RequestAssignmentBase(BaseModel):
    department_id: int
    expert_id: int
    due_date: Optional[datetime] = None
    is_primary: bool = False

class CommunicationTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    requires_response: bool = False
    default_deadline_hours: Optional[int] = None

class InterdepartmentalCommunicationBase(BaseModel):
    subject: str
    content: str
    priority: PriorityEnum = PriorityEnum.medium
    due_date: Optional[datetime] = None

# Create Schemas
class OpinionRequestCreate(OpinionRequestBase):
    department_id: int

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        description: str = Form(...),
        priority: PriorityEnum = Form(...),
        department_id: int = Form(...),
        category_id: int = Form(...),
        sub_category_id: Optional[int] = Form(None),
        due_date: Optional[datetime] = Form(None),
        request_statement: Optional[str] = Form(None),
        challenges_opportunities: Optional[str] = Form(None),
        subject_content: Optional[str] = Form(None),
        alternative_options: Optional[str] = Form(None),
        expected_impact: Optional[str] = Form(None),
        potential_risks: Optional[str] = Form(None),
        studies_statistics: Optional[str] = Form(None),
        legal_financial_opinions: Optional[str] = Form(None),
        stakeholder_feedback: Optional[str] = Form(None),
        work_plan: Optional[str] = Form(None),
        decision_draft: Optional[str] = Form(None)
    ):
        return cls(
            title=title,
            description=description,
            priority=priority,
            department_id=department_id,
            category_id=category_id,
            sub_category_id=sub_category_id,
            due_date=due_date,
            request_statement=request_statement,
            challenges_opportunities=challenges_opportunities,
            subject_content=subject_content,
            alternative_options=alternative_options,
            expected_impact=expected_impact,
            potential_risks=potential_risks,
            studies_statistics=studies_statistics,
            legal_financial_opinions=legal_financial_opinions,
            stakeholder_feedback=stakeholder_feedback,
            work_plan=work_plan,
            decision_draft=decision_draft
        )

class DocumentCreate(DocumentBase):
    opinion_request_id: int
    uploaded_by: int

class RemarkCreate(RemarkBase):
    opinion_request_id: int
    user_id: int

class OpinionCreate(OpinionBase):
    opinion_request_id: int
    department_id: int
    expert_id: int

class RequestAssignmentCreate(RequestAssignmentBase):
    opinion_request_id: int
    assigned_by: int

class InterdepartmentalCommunicationCreate(InterdepartmentalCommunicationBase):
    opinion_request_id: int
    communication_type_id: int
    from_department_id: int
    to_department_id: int
    from_user_id: int
    to_user_id: int
    parent_communication_id: Optional[int] = None

# Update Schemas
class OpinionRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    due_date: Optional[datetime] = None
    request_statement: Optional[str] = None
    challenges_opportunities: Optional[str] = None
    subject_content: Optional[str] = None
    alternative_options: Optional[str] = None
    expected_impact: Optional[str] = None
    potential_risks: Optional[str] = None
    studies_statistics: Optional[str] = None
    legal_financial_opinions: Optional[str] = None
    stakeholder_feedback: Optional[str] = None
    work_plan: Optional[str] = None
    decision_draft: Optional[str] = None

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
        from_attributes = True

class CategoryInDB(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SubCategoryInDB(SubCategoryBase):
    id: int
    created_at: datetime
    category: CategoryInDB

    class Config:
        from_attributes = True

class DocumentInDB(DocumentBase):
    id: int
    opinion_request_id: int
    uploaded_by: int
    created_at: datetime
    uploader: Optional[User] = None

    class Config:
        from_attributes = True

class RemarkInDB(RemarkBase):
    id: int
    opinion_request_id: int
    user_id: int
    created_at: datetime
    user: Optional[User] = None

    class Config:
        from_attributes = True

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
    department: Optional[Department] = None
    expert: Optional[User] = None
    reviewer: Optional[User] = None

    class Config:
        from_attributes = True


class RequestAssignmentInDB(RequestAssignmentBase):
    id: int
    opinion_request_id: int
    assigned_by: int
    status_id: int
    created_at: datetime
    department: Optional[Department] = None
    assigner: Optional[User] = None
    expert: Optional[User] = None
    status: Optional[WorkflowStatusInDB] = None

    class Config:
        from_attributes = True

class OpinionRequestInDB(OpinionRequestBase):
    id: int
    reference_number: str
    requester_id: int
    department_id: int
    current_status_id: int
    created_at: datetime
    updated_at: datetime
    version: int
    is_deleted: bool
    deleted_at: Optional[datetime]
    deleted_by: Optional[int]
    
    documents: List[DocumentInDB] = []
    remarks: List[RemarkInDB] = []
    opinions: List[OpinionInDB] = []
    assignments: List[RequestAssignmentInDB] = []
    category_rel: Optional[CategoryInDB] = None
    subcategory_rel: Optional[SubCategoryInDB] = None
    requester: Optional[User] = None
    department: Optional[Department] = None
    current_status: Optional[WorkflowStatusInDB] = None

    class Config:
        from_attributes = True
        
# In app/schemas/opinion.py, add:

class WorkflowHistoryBase(BaseModel):
    action_type: str
    action_details: Optional[Dict[str, Any]] = None

class WorkflowHistoryCreate(WorkflowHistoryBase):
    opinion_request_id: int
    action_by: int
    from_status_id: Optional[int] = None
    to_status_id: Optional[int] = None

class WorkflowHistoryInDB(WorkflowHistoryBase):
    id: int
    opinion_request_id: int
    action_by: int
    from_status_id: Optional[int]
    to_status_id: Optional[int]
    created_at: datetime
    action_type: str
    action_details: Optional[Dict[str, Any]] = None
    
    # Include these relations with proper typing
    actor: Optional[UserBase] = None
    from_status: Optional[WorkflowStatusInDB] = None
    to_status: Optional[WorkflowStatusInDB] = None

    class Config:
        from_attributes = True

# Additional Schemas
class OpinionRequestWithDetails(OpinionRequestInDB):
    # Explicitly type workflow_history as a list of WorkflowHistoryInDB
    workflow_history: List[WorkflowHistoryInDB] = []
    communications: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True

class OpinionReview(BaseModel):
    is_approved: bool
    comments: Optional[str] = None

class OpinionRequestList(BaseModel):
    total: int
    items: List[OpinionRequestInDB]

    class Config:
        from_attributes = True
        
# In app/schemas/opinion.py

class WorkflowStatusBase(BaseModel):
    name: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowStatusList(BaseModel):
    total: int
    items: List[WorkflowStatusBase]

    class Config:
        from_attributes = True

# Category Schemas
class SubCategoryBase(BaseModel):
    id: int
    name: str
    category_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryBase(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryWithSubcategories(CategoryBase):
    subcategories: List[SubCategoryBase] = []

    class Config:
        from_attributes = True

class CategoryList(BaseModel):
    total: int
    items: List[CategoryWithSubcategories]

    class Config:
        from_attributes = True

OpinionInDB.model_rebuild()
DocumentInDB.model_rebuild()
RemarkInDB.model_rebuild()
RequestAssignmentInDB.model_rebuild()
WorkflowHistoryInDB.model_rebuild()
OpinionRequestInDB.model_rebuild()
OpinionRequestWithDetails.model_rebuild()