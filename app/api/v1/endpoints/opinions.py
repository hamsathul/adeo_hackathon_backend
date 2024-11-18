# app/api/v1/endpoints/opinions.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from fastapi.encoders import jsonable_encoder
import json
from fastapi.responses import FileResponse
from pydantic_core import ValidationError
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import uuid
import os
import logging

from app.api import deps
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.auth import User
from app.models.department import Department
from app.models.opinion import (
    OpinionRequest,
    Document,
    Category,
    SubCategory,
    Remark,
    RequestAssignment,
    Opinion,
    WorkflowStatus,
    WorkflowHistory,
    CommunicationType,
    InterdepartmentalCommunication
)
from app.schemas.base import UserBase, DepartmentBase
from app.schemas.opinion import (
    OpinionRequestCreate,
    OpinionRequestInDB,
    OpinionRequestUpdate,
    OpinionCreate,
    OpinionInDB,
    OpinionUpdate,
    OpinionReview,
    OpinionRequestWithDetails,
    DocumentInDB,
    RemarkInDB,
    WorkflowHistoryInDB,
    PriorityEnum
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

@router.post("/requests/")
async def create_opinion_request(
    *,
    db: Session = Depends(get_db),
    files: Optional[List[UploadFile]] = File(default=None),
    request_data: str = Form(...),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new opinion request with optional multiple file attachments."""
    try:
        logging.debug(f"Request data: {request_data}")
        
        try:
            request_dict = json.loads(request_data)
            request_data = OpinionRequestCreate(**request_dict)
        except json.JSONDecodeError:
            raise HTTPException(status_code=422, detail="Invalid JSON in request_data")
        
        logging.debug(f"Parsed request data: {request_dict}")

        # Validate category and subcategory
        category = db.query(Category).filter(Category.id == request_data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

        if request_data.sub_category_id:
            subcategory = db.query(SubCategory).filter(
                SubCategory.id == request_data.sub_category_id,
                SubCategory.category_id == request_data.category_id
            ).first()
            if not subcategory:
                raise HTTPException(status_code=404, detail="Invalid subcategory for the selected category")

        reference_number = f"OPN-{uuid.uuid4().hex[:8].upper()}"
        initial_status = db.query(WorkflowStatus).filter(WorkflowStatus.name == "unassigned").first()
        if not initial_status:
            raise HTTPException(status_code=404, detail="Initial status not found")

        # Create opinion request with new fields
        opinion_request = OpinionRequest(
            reference_number=reference_number,
            title=request_data.title,
            description=request_data.description,
            requester_id=current_user.id,
            department_id=request_data.department_id,
            category_id=request_data.category_id,
            sub_category_id=request_data.sub_category_id,
            priority=request_data.priority,
            current_status_id=initial_status.id,
            due_date=request_data.due_date,
            request_statement=request_data.request_statement,
            challenges_opportunities=request_data.challenges_opportunities,
            subject_content=request_data.subject_content,
            alternative_options=request_data.alternative_options,
            expected_impact=request_data.expected_impact,
            potential_risks=request_data.potential_risks,
            studies_statistics=request_data.studies_statistics,
            legal_financial_opinions=request_data.legal_financial_opinions,
            stakeholder_feedback=request_data.stakeholder_feedback,
            work_plan=request_data.work_plan,
            decision_draft=request_data.decision_draft,
            version=1
        )
        
        db.add(opinion_request)
        db.flush()

        # Handle file uploads
        if files:
            upload_dir = f"uploads/opinion_requests/{opinion_request.id}"
            os.makedirs(upload_dir, exist_ok=True)

            for file in files:
                try:
                    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
                    file_path = os.path.join(upload_dir, safe_filename)
                    
                    contents = await file.read()
                    with open(file_path, "wb") as f:
                        f.write(contents)

                    document = Document(
                        opinion_request_id=opinion_request.id,
                        file_name=file.filename,
                        file_path=file_path,
                        file_type=file.content_type,
                        file_size=len(contents),
                        file_url=f"/uploads/opinion_requests/{opinion_request.id}/{safe_filename}",
                        uploaded_by=current_user.id
                    )
                    db.add(document)

                except Exception as e:
                    logging.error(f"Error during file upload: {e}")
                    raise HTTPException(status_code=400, detail=f"Error uploading file {file.filename}: {str(e)}")

        # Create workflow history
        history = WorkflowHistory(
            opinion_request_id=opinion_request.id,
            action_type="created",
            action_by=current_user.id,
            from_status_id=None,
            to_status_id=initial_status.id,
            action_details={
                "message": "Opinion request created",
                "files_uploaded": len(files) if files else 0
            }
        )
        db.add(history)

        db.commit()
        db.refresh(opinion_request)
        
        return opinion_request

    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        db.rollback()
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException as e:
        logging.error(f"HTTP exception: {e}")
        db.rollback()
        raise
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


    
@router.get("/requests/", response_model=List[OpinionRequestWithDetails])
async def get_opinion_requests(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    department_id: Optional[int] = None,
    category_id: Optional[int] = None,  # Added
    sub_category_id: Optional[int] = None,  # Added
    priority: Optional[PriorityEnum] = None,  # Added
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get list of opinion requests with filtering options."""
    try:
        query = db.query(OpinionRequest).filter(OpinionRequest.is_deleted == False)
        
        # Apply filters
        if status:
            query = query.join(WorkflowStatus).filter(WorkflowStatus.name == status)
        
        if department_id:
            query = query.filter(OpinionRequest.department_id == department_id)
            
        if category_id:
            query = query.filter(OpinionRequest.category_id == category_id)
            
        if sub_category_id:
            query = query.filter(OpinionRequest.sub_category_id == sub_category_id)
            
        if priority:
            query = query.filter(OpinionRequest.priority == priority)
            
        if from_date:
            query = query.filter(OpinionRequest.created_at >= from_date)
            
        if to_date:
            query = query.filter(OpinionRequest.created_at <= to_date)
        
        # Get total count for pagination
        total = query.count()
        
        # Get requests with related data
        requests = (
            query
            .options(
                joinedload(OpinionRequest.category_rel),
                joinedload(OpinionRequest.subcategory_rel),
                joinedload(OpinionRequest.requester),
                joinedload(OpinionRequest.department),
                joinedload(OpinionRequest.current_status),
                joinedload(OpinionRequest.documents),
                joinedload(OpinionRequest.remarks),
                joinedload(OpinionRequest.opinions),
                joinedload(OpinionRequest.assignments),
                joinedload(OpinionRequest.workflow_history)
            )
            .order_by(OpinionRequest.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return requests

    except Exception as e:
        logging.error(f"Error fetching opinion requests: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/requests/{request_id}", response_model=OpinionRequestWithDetails)
async def get_opinion_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific opinion request."""
    try:
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == request_id,
                OpinionRequest.is_deleted == False
            )
            .options(
                joinedload(OpinionRequest.category_rel),
                joinedload(OpinionRequest.subcategory_rel),
                joinedload(OpinionRequest.requester),
                joinedload(OpinionRequest.department),
                joinedload(OpinionRequest.current_status),
                joinedload(OpinionRequest.documents),
                joinedload(OpinionRequest.remarks),
                joinedload(OpinionRequest.opinions),
                joinedload(OpinionRequest.assignments),
                joinedload(OpinionRequest.workflow_history)
            )
            .first()
        )
        
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        return request

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching opinion request {request_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/requests/{request_id}", response_model=OpinionRequestInDB)
async def update_opinion_request(
    *,
    request_id: int,
    request_update: OpinionRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing opinion request."""
    try:
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == request_id,
                OpinionRequest.is_deleted == False
            )
            .first()
        )
        
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        # Validate category and subcategory if being updated
        if request_update.category_id is not None:
            category = db.query(Category).filter(Category.id == request_update.category_id).first()
            if not category:
                raise HTTPException(status_code=404, detail="Category not found")

            request.category_id = request_update.category_id
            
            # Reset subcategory if category changes
            if request_update.sub_category_id is None:
                request.sub_category_id = None

        if request_update.sub_category_id is not None:
            subcategory = db.query(SubCategory).filter(
                SubCategory.id == request_update.sub_category_id,
                SubCategory.category_id == (request_update.category_id or request.category_id)
            ).first()
            if not subcategory:
                raise HTTPException(status_code=404, detail="Invalid subcategory for the selected category")
            
            request.sub_category_id = request_update.sub_category_id
        
        # Update basic fields
        update_data = request_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(request, field) and value is not None:
                setattr(request, field, value)
        
        # Update version
        request.version += 1
        request.updated_at = datetime.utcnow()
        
        # Create history record for update
        history = WorkflowHistory(
            opinion_request_id=request_id,
            action_type="updated",
            action_by=current_user.id,
            from_status_id=request.current_status_id,
            to_status_id=request.current_status_id,
            action_details={
                "updated_fields": list(update_data.keys()),
                "version": request.version
            }
        )
        db.add(history)
            
        db.commit()
        db.refresh(request)
        return request

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating opinion request {request_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
# Admin and Assignment Endpoints
@router.post("/requests/{request_id}/assign", response_model=OpinionRequestInDB)
async def assign_request(
    *,
    request_id: int,
    department_id: int = Body(...),
    expert_id: Optional[int] = Body(None),
    due_date: Optional[datetime] = Body(None),
    is_primary: bool = Body(False),
    remarks: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign request to department/expert."""
    try:
        # Get request and verify it exists and isn't deleted
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == request_id,
                OpinionRequest.is_deleted == False
            )
            .first()
        )
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        # Verify department exists
        department = db.query(Department).filter(Department.id == department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Verify expert if provided
        if expert_id:
            expert = db.query(User).filter(
                User.id == expert_id,
                User.department_id == department_id,
                User.is_active == True
            ).first()
            if not expert:
                raise HTTPException(
                    status_code=404,
                    detail="Expert not found or not active in specified department"
                )
        
        # Get or create assigned status
        new_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == ("assigned_to_expert" if expert_id else "assigned_to_department")
        ).first()
        if not new_status:
            raise HTTPException(status_code=404, detail="Assignment status not found")
        
        # Check if there's already a primary assignment
        if is_primary:
            existing_primary = db.query(RequestAssignment).filter(
                RequestAssignment.opinion_request_id == request_id,
                RequestAssignment.is_primary == True
            ).first()
            if existing_primary:
                existing_primary.is_primary = False
        
        # Create assignment
        assignment = RequestAssignment(
            opinion_request_id=request_id,
            department_id=department_id,
            assigned_by=current_user.id,
            expert_id=expert_id,
            status_id=new_status.id,
            due_date=due_date,
            is_primary=is_primary,
            created_at=datetime.utcnow()
        )
        db.add(assignment)
        
        # Add remark if provided
        if remarks:
            remark = Remark(
                opinion_request_id=request_id,
                user_id=current_user.id,
                content=remarks
            )
            db.add(remark)
        
        # Update request status and tracking
        old_status_id = request.current_status_id
        request.current_status_id = new_status.id
        request.updated_at = datetime.utcnow()
        request.version += 1
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=request_id,
            action_type="assigned",
            action_by=current_user.id,
            from_status_id=old_status_id,
            to_status_id=new_status.id,
            action_details={
                "department_id": department_id,
                "expert_id": expert_id,
                "is_primary": is_primary,
                "due_date": due_date.isoformat() if due_date else None,
                "remarks": remarks,
                "version": request.version
            }
        )
        db.add(history)
        
        # Create interdepartmental communication if needed
        if department_id != request.department_id:
            communication = InterdepartmentalCommunication(
                opinion_request_id=request_id,
                from_department_id=request.department_id,
                to_department_id=department_id,
                from_user_id=current_user.id,
                to_user_id=expert_id if expert_id else None,
                subject=f"Opinion Request Assignment: {request.reference_number}",
                content=remarks if remarks else "Request assigned for review",
                priority=request.priority,
                status="pending",
                due_date=due_date
            )
            db.add(communication)
        
        db.commit()
        
        # Refresh and return with all relationships loaded
        db.refresh(request)
        return request
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error assigning request {request_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/requests/{request_id}/reassign", response_model=OpinionRequestInDB)
async def reassign_request(
    *,
    request_id: int,
    assignment_id: int = Body(...),
    expert_id: int = Body(...),
    due_date: Optional[datetime] = Body(None),
    remarks: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reassign request to different expert within same department."""
    try:
        # Get and verify assignment
        assignment = db.query(RequestAssignment).filter(
            RequestAssignment.id == assignment_id,
            RequestAssignment.opinion_request_id == request_id
        ).first()
        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")
        
        # Verify new expert
        expert = db.query(User).filter(
            User.id == expert_id,
            User.department_id == assignment.department_id,
            User.is_active == True
        ).first()
        if not expert:
            raise HTTPException(
                status_code=404,
                detail="Expert not found or not active in assigned department"
            )
        
        # Get request
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == request_id,
                OpinionRequest.is_deleted == False
            )
            .first()
        )
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        # Update assignment
        old_expert_id = assignment.expert_id
        assignment.expert_id = expert_id
        if due_date:
            assignment.due_date = due_date
        assignment.updated_at = datetime.utcnow()
        
        # Add remark if provided
        if remarks:
            remark = Remark(
                opinion_request_id=request_id,
                user_id=current_user.id,
                content=remarks
            )
            db.add(remark)
        
        # Update request tracking
        request.updated_at = datetime.utcnow()
        request.version += 1
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=request_id,
            action_type="reassigned",
            action_by=current_user.id,
            from_status_id=request.current_status_id,
            to_status_id=request.current_status_id,
            action_details={
                "assignment_id": assignment_id,
                "old_expert_id": old_expert_id,
                "new_expert_id": expert_id,
                "due_date": due_date.isoformat() if due_date else None,
                "remarks": remarks,
                "version": request.version
            }
        )
        db.add(history)
        
        db.commit()
        db.refresh(request)
        return request

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error reassigning request {request_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
# Opinion Management
# Opinion Management Endpoints
@router.post("/opinions/", response_model=OpinionInDB)
async def create_opinion(
    *,
    db: Session = Depends(get_db),
    opinion_data: OpinionCreate,
    remarks: Optional[str] = Body(None),
    files: Optional[List[UploadFile]] = File(default=None),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new opinion."""
    try:
        # Verify request exists and user is assigned
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == opinion_data.opinion_request_id,
                OpinionRequest.is_deleted == False
            )
            .first()
        )
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
            
        # Verify assignment
        assignment = db.query(RequestAssignment).filter(
            RequestAssignment.opinion_request_id == opinion_data.opinion_request_id,
            RequestAssignment.expert_id == current_user.id,
            RequestAssignment.department_id == opinion_data.department_id
        ).first()
        
        if not assignment:
            raise HTTPException(
                status_code=403, 
                detail="You are not assigned to this request"
            )

        # Create opinion
        opinion = Opinion(
            opinion_request_id=opinion_data.opinion_request_id,
            department_id=opinion_data.department_id,
            expert_id=current_user.id,
            content=opinion_data.content,
            recommendation=opinion_data.recommendation,
            status='draft',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(opinion)
        db.flush()  # Get opinion ID
        
        # Handle file attachments if any
        if files:
            upload_dir = f"uploads/opinion_requests/{request.id}/opinions/{opinion.id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            for file in files:
                try:
                    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
                    file_path = os.path.join(upload_dir, safe_filename)
                    
                    contents = await file.read()
                    with open(file_path, "wb") as f:
                        f.write(contents)

                    document = Document(
                        opinion_request_id=request.id,
                        file_name=file.filename,
                        file_path=file_path,
                        file_type=file.content_type,
                        file_size=len(contents),
                        file_url=f"/uploads/opinion_requests/{request.id}/opinions/{opinion.id}/{safe_filename}",
                        uploaded_by=current_user.id
                    )
                    db.add(document)

                except Exception as e:
                    logging.error(f"Error during file upload: {e}")
                    raise HTTPException(status_code=400, detail=f"Error uploading file {file.filename}: {str(e)}")
        
        # Add remark if provided
        if remarks:
            remark = Remark(
                opinion_request_id=request.id,
                user_id=current_user.id,
                content=remarks
            )
            db.add(remark)
        
        # Update request status and version
        new_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == "opinion_draft_created"
        ).first()
        
        old_status_id = request.current_status_id
        request.current_status_id = new_status.id
        request.updated_at = datetime.utcnow()
        request.version += 1
        
        # Update assignment status
        assignment.status_id = new_status.id
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=request.id,
            action_type="opinion_created",
            action_by=current_user.id,
            from_status_id=old_status_id,
            to_status_id=new_status.id,
            action_details={
                "opinion_id": opinion.id,
                "department_id": opinion_data.department_id,
                "has_recommendation": opinion_data.recommendation is not None,
                "files_attached": len(files) if files else 0,
                "remarks": remarks,
                "version": request.version
            }
        )
        db.add(history)
        
        db.commit()
        db.refresh(opinion)
        return opinion
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating opinion: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/opinions/{opinion_id}", response_model=OpinionInDB)
async def update_opinion(
    *,
    opinion_id: int,
    opinion_update: OpinionUpdate,
    remarks: Optional[str] = Body(None),
    files: Optional[List[UploadFile]] = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing opinion."""
    try:
        # Get and verify opinion
        opinion = (
            db.query(Opinion)
            .filter(Opinion.id == opinion_id)
            .first()
        )
        if not opinion:
            raise HTTPException(status_code=404, detail="Opinion not found")
            
        # Verify ownership
        if opinion.expert_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this opinion")
            
        # Get request
        request = (
            db.query(OpinionRequest)
            .filter(OpinionRequest.id == opinion.opinion_request_id)
            .first()
        )
        
        # Update opinion fields
        update_data = opinion_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(opinion, field) and value is not None:
                setattr(opinion, field, value)
                
        opinion.updated_at = datetime.utcnow()
        
        # Handle new files if any
        if files:
            upload_dir = f"uploads/opinion_requests/{request.id}/opinions/{opinion.id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            for file in files:
                try:
                    safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
                    file_path = os.path.join(upload_dir, safe_filename)
                    
                    contents = await file.read()
                    with open(file_path, "wb") as f:
                        f.write(contents)

                    document = Document(
                        opinion_request_id=request.id,
                        file_name=file.filename,
                        file_path=file_path,
                        file_type=file.content_type,
                        file_size=len(contents),
                        file_url=f"/uploads/opinion_requests/{request.id}/opinions/{opinion.id}/{safe_filename}",
                        uploaded_by=current_user.id
                    )
                    db.add(document)

                except Exception as e:
                    logging.error(f"Error during file upload: {e}")
                    raise HTTPException(status_code=400, detail=f"Error uploading file {file.filename}: {str(e)}")
        
        # Add remark if provided
        if remarks:
            remark = Remark(
                opinion_request_id=request.id,
                user_id=current_user.id,
                content=remarks
            )
            db.add(remark)
        
        # Update request version
        request.updated_at = datetime.utcnow()
        request.version += 1
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=request.id,
            action_type="opinion_updated",
            action_by=current_user.id,
            from_status_id=request.current_status_id,
            to_status_id=request.current_status_id,
            action_details={
                "opinion_id": opinion.id,
                "updated_fields": list(update_data.keys()),
                "files_attached": len(files) if files else 0,
                "remarks": remarks,
                "version": request.version
            }
        )
        db.add(history)
        
        db.commit()
        db.refresh(opinion)
        return opinion
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating opinion {opinion_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/opinions/{opinion_id}/submit", response_model=OpinionInDB)
async def submit_opinion(
    *,
    opinion_id: int,
    remarks: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Submit an opinion for review."""
    try:
        # Get and verify opinion
        opinion = (
            db.query(Opinion)
            .filter(Opinion.id == opinion_id)
            .first()
        )
        if not opinion:
            raise HTTPException(status_code=404, detail="Opinion not found")
            
        # Verify ownership
        if opinion.expert_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to submit this opinion")
            
        # Verify opinion is in draft status
        if opinion.status != 'draft':
            raise HTTPException(status_code=400, detail="Only draft opinions can be submitted")
            
        # Get request
        request = (
            db.query(OpinionRequest)
            .filter(OpinionRequest.id == opinion.opinion_request_id)
            .first()
        )
        
        # Update opinion status
        opinion.status = 'submitted'
        opinion.updated_at = datetime.utcnow()
        
        # Update request status
        new_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == "opinion_submitted"
        ).first()
        
        old_status_id = request.current_status_id
        request.current_status_id = new_status.id
        request.updated_at = datetime.utcnow()
        request.version += 1
        
        # Add remark if provided
        if remarks:
            remark = Remark(
                opinion_request_id=request.id,
                user_id=current_user.id,
                content=remarks
            )
            db.add(remark)
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=request.id,
            action_type="opinion_submitted",
            action_by=current_user.id,
            from_status_id=old_status_id,
            to_status_id=new_status.id,
            action_details={
                "opinion_id": opinion.id,
                "remarks": remarks,
                "version": request.version
            }
        )
        db.add(history)
        
        db.commit()
        db.refresh(opinion)
        return opinion
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error submitting opinion {opinion_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Document Management
# Document Management Endpoints
@router.post("/requests/{request_id}/documents/", response_model=List[DocumentInDB])
async def upload_documents(
    *,
    request_id: int,
    files: List[UploadFile] = File(...),
    document_type: Optional[str] = Form(None),
    remarks: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload documents for an opinion request."""
    try:
        # Verify request exists and is accessible
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == request_id,
                OpinionRequest.is_deleted == False
            )
            .first()
        )
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")

        # Verify file types and sizes
        allowed_types = ['pdf', 'doc', 'docx', 'xls', 'xlsx']
        max_file_size = 10 * 1024 * 1024  # 10MB

        uploaded_documents = []
        upload_dir = f"uploads/opinion_requests/{request_id}"
        os.makedirs(upload_dir, exist_ok=True)

        for file in files:
            try:
                # Verify file type
                file_ext = file.filename.split('.')[-1].lower()
                if file_ext not in allowed_types:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File type .{file_ext} not allowed. Allowed types: {', '.join(allowed_types)}"
                    )

                # Read file content
                contents = await file.read()
                
                # Verify file size
                if len(contents) > max_file_size:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File {file.filename} exceeds maximum size of 10MB"
                    )

                # Generate safe filename and save
                safe_filename = f"{uuid.uuid4().hex}_{file.filename}"
                file_path = os.path.join(upload_dir, safe_filename)
                
                with open(file_path, "wb") as file_object:
                    file_object.write(contents)

                # Create document record
                document = Document(
                    opinion_request_id=request_id,
                    file_name=file.filename,
                    file_path=file_path,
                    file_type=file.content_type,
                    file_size=len(contents),
                    file_url=f"/uploads/opinion_requests/{request_id}/{safe_filename}",
                    uploaded_by=current_user.id,
                    created_at=datetime.utcnow()
                )
                db.add(document)
                uploaded_documents.append(document)

            except HTTPException:
                raise
            except Exception as e:
                logging.error(f"Error uploading file {file.filename}: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Error uploading file {file.filename}: {str(e)}"
                )

        # Add remark if provided
        if remarks:
            remark = Remark(
                opinion_request_id=request_id,
                user_id=current_user.id,
                content=remarks
            )
            db.add(remark)

        # Update request version
        request.version += 1
        request.updated_at = datetime.utcnow()

        # Record history
        history = WorkflowHistory(
            opinion_request_id=request_id,
            action_type="documents_uploaded",
            action_by=current_user.id,
            from_status_id=request.current_status_id,
            to_status_id=request.current_status_id,
            action_details={
                "uploaded_files": [doc.file_name for doc in uploaded_documents],
                "document_type": document_type,
                "remarks": remarks,
                "version": request.version
            }
        )
        db.add(history)

        db.commit()
        return uploaded_documents

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error uploading documents for request {request_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    remarks: Optional[str] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a document."""
    try:
        # Get and verify document
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get request
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == document.opinion_request_id,
                OpinionRequest.is_deleted == False
            )
            .first()
        )
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")

        # Verify permissions (only uploader or admin can delete)
        if document.uploaded_by != current_user.id and not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")

        # Delete physical file
        try:
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
        except Exception as e:
            logging.error(f"Error deleting file {document.file_path}: {e}")
            # Continue with database deletion even if file deletion fails

        # Add remark if provided
        if remarks:
            remark = Remark(
                opinion_request_id=request.id,
                user_id=current_user.id,
                content=remarks
            )
            db.add(remark)

        # Update request version
        request.version += 1
        request.updated_at = datetime.utcnow()

        # Record history before deleting document
        history = WorkflowHistory(
            opinion_request_id=request.id,
            action_type="document_deleted",
            action_by=current_user.id,
            from_status_id=request.current_status_id,
            to_status_id=request.current_status_id,
            action_details={
                "document_id": document.id,
                "file_name": document.file_name,
                "file_type": document.file_type,
                "remarks": remarks,
                "version": request.version
            }
        )
        db.add(history)

        # Delete document record
        db.delete(document)
        db.commit()

        return {"message": "Document deleted successfully"}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a document."""
    try:
        # Get and verify document
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Verify request is not deleted
        request = (
            db.query(OpinionRequest)
            .filter(
                OpinionRequest.id == document.opinion_request_id,
                OpinionRequest.is_deleted == False
            )
            .first()
        )
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")

        # Verify file exists
        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="File not found on server")

        # Record download history
        history = WorkflowHistory(
            opinion_request_id=request.id,
            action_type="document_downloaded",
            action_by=current_user.id,
            from_status_id=request.current_status_id,
            to_status_id=request.current_status_id,
            action_details={
                "document_id": document.id,
                "file_name": document.file_name,
                "version": request.version
            }
        )
        db.add(history)
        db.commit()

        return FileResponse(
            document.file_path,
            filename=document.file_name,
            media_type=document.file_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading document {document_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
# Statistics Endpoints
@router.get("/statistics/department/{department_id}")
async def get_department_statistics(
    department_id: int,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get statistics for a department."""
    try:
        query = db.query(OpinionRequest).filter(
            OpinionRequest.department_id == department_id
        )
        
        if from_date:
            query = query.filter(OpinionRequest.created_at >= from_date)
        if to_date:
            query = query.filter(OpinionRequest.created_at <= to_date)
        
        total_requests = query.count()
        
        completed_requests = query.join(WorkflowStatus).filter(
            WorkflowStatus.name.in_(['head_approved', 'completed'])
        ).count()
        
        pending_requests = query.join(WorkflowStatus).filter(
            WorkflowStatus.name.not_in(['head_approved', 'completed', 'rejected'])
        ).count()
        
        # Calculate average completion time
        completed_requests_data = query.join(WorkflowStatus).filter(
            WorkflowStatus.name.in_(['head_approved', 'completed'])
        ).all()
        
        total_time = sum(
            (r.updated_at - r.created_at).total_seconds() 
            for r in completed_requests_data
        )
        avg_completion_time = (
            total_time / len(completed_requests_data) 
            if completed_requests_data else 0
        )
        
        return {
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "pending_requests": pending_requests,
            "average_completion_time": avg_completion_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))