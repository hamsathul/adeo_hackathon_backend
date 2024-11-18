# app/api/v1/endpoints/opinions.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import os

from app.api import deps
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.auth import User
from app.models.opinion import (
    OpinionRequest,
    Document,
    RequestAssignment,
    Opinion,
    WorkflowStatus,
    WorkflowHistory
)
from app.schemas.opinion import (
    OpinionRequestCreate,
    OpinionRequestInDB,
    OpinionRequestUpdate,
    OpinionCreate,
    OpinionInDB,
    OpinionUpdate,
    OpinionReview,
    OpinionRequestWithDetails,
    DocumentInDB
)

router = APIRouter()

# Opinion Request Endpoints
@router.post("/requests/", response_model=OpinionRequestInDB)
async def create_opinion_request(
    *,
    db: Session = Depends(get_db),
    files: List[UploadFile] = File(None),
    request_data: OpinionRequestCreate = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new opinion request with optional file attachments."""
    try:
        # Create unique reference number
        reference_number = f"OPN-{uuid.uuid4().hex[:8].upper()}"
        
        # Get initial status
        initial_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == "unassigned"
        ).first()
        
        # Create opinion request
        opinion_request = OpinionRequest(
            reference_number=reference_number,
            title=request_data.title,
            description=request_data.description,
            requester_id=current_user.id,
            department_id=request_data.department_id,
            priority=request_data.priority,
            current_status_id=initial_status.id,
            due_date=request_data.due_date
        )
        
        db.add(opinion_request)
        db.flush()
        
        # Handle file uploads if any
        if files:
            upload_dir = f"uploads/opinion_requests/{opinion_request.id}"
            os.makedirs(upload_dir, exist_ok=True)
            
            for file in files:
                file_path = os.path.join(upload_dir, file.filename)
                with open(file_path, "wb+") as file_object:
                    file_object.write(file.file.read())
                
                document = Document(
                    opinion_request_id=opinion_request.id,
                    file_name=file.filename,
                    file_path=file_path,
                    file_type=file.content_type,
                    file_size=os.path.getsize(file_path),
                    uploaded_by=current_user.id
                )
                db.add(document)
        
        # Create workflow history
        history = WorkflowHistory(
            opinion_request_id=opinion_request.id,
            action_type="created",
            action_by=current_user.id,
            from_status_id=None,
            to_status_id=initial_status.id,
            action_details={"message": "Opinion request created"}
        )
        db.add(history)
        
        db.commit()
        return opinion_request

    except Exception as e:
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
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get list of opinion requests with filtering options."""
    try:
        query = db.query(OpinionRequest)
        
        # Apply filters
        if status:
            query = query.join(WorkflowStatus).filter(WorkflowStatus.name == status)
        
        if department_id:
            query = query.filter(OpinionRequest.department_id == department_id)
            
        if from_date:
            query = query.filter(OpinionRequest.created_at >= from_date)
            
        if to_date:
            query = query.filter(OpinionRequest.created_at <= to_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        requests = query.order_by(OpinionRequest.created_at.desc()).offset(skip).limit(limit).all()
        
        return requests

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/requests/{request_id}", response_model=OpinionRequestWithDetails)
async def get_opinion_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed information about a specific opinion request."""
    try:
        request = db.query(OpinionRequest).filter(
            OpinionRequest.id == request_id
        ).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        return request

    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

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
        request = db.query(OpinionRequest).filter(
            OpinionRequest.id == request_id
        ).first()
        
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        # Update fields if provided
        if request_update.title is not None:
            request.title = request_update.title
        if request_update.description is not None:
            request.description = request_update.description
        if request_update.priority is not None:
            request.priority = request_update.priority
        if request_update.due_date is not None:
            request.due_date = request_update.due_date
            
        db.commit()
        return request

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
# Admin and Assignment Endpoints
@router.post("/requests/{request_id}/assign", response_model=OpinionRequestInDB)
async def assign_request(
    *,
    request_id: int,
    department_id: int = Body(...),
    expert_id: Optional[int] = Body(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign request to department/expert."""
    try:
        # Get request and new status
        request = db.query(OpinionRequest).filter(OpinionRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        new_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == "assigned_to_department"
        ).first()
        
        # Create assignment
        assignment = RequestAssignment(
            opinion_request_id=request_id,
            department_id=department_id,
            assigned_by=current_user.id,
            expert_id=expert_id,
            status_id=new_status.id
        )
        db.add(assignment)
        
        # Update request status
        old_status_id = request.current_status_id
        request.current_status_id = new_status.id
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=request_id,
            action_type="assigned",
            action_by=current_user.id,
            from_status_id=old_status_id,
            to_status_id=new_status.id,
            action_details={
                "department_id": department_id,
                "expert_id": expert_id
            }
        )
        db.add(history)
        
        db.commit()
        return request
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/requests/{request_id}/assign-expert", response_model=OpinionRequestInDB)
async def assign_expert(
    *,
    request_id: int,
    expert_id: int = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign request to expert."""
    try:
        # Get request and assignment
        request = db.query(OpinionRequest).filter(OpinionRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
            
        assignment = db.query(RequestAssignment).filter(
            RequestAssignment.opinion_request_id == request_id
        ).first()
        
        # Update status
        new_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == "assigned_to_expert"
        ).first()
        
        old_status_id = request.current_status_id
        request.current_status_id = new_status.id
        
        # Update assignment
        assignment.expert_id = expert_id
        assignment.status_id = new_status.id
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=request_id,
            action_type="expert_assigned",
            action_by=current_user.id,
            from_status_id=old_status_id,
            to_status_id=new_status.id,
            action_details={"expert_id": expert_id}
        )
        db.add(history)
        
        db.commit()
        return request
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Opinion Management
@router.post("/opinions/", response_model=OpinionInDB)
async def create_opinion(
    *,
    opinion_data: OpinionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new opinion."""
    try:
        # Create opinion
        opinion = Opinion(
            opinion_request_id=opinion_data.opinion_request_id,
            department_id=opinion_data.department_id,
            expert_id=current_user.id,
            content=opinion_data.content,
            recommendation=opinion_data.recommendation,
            status='draft'
        )
        db.add(opinion)
        
        # Update request status
        request = db.query(OpinionRequest).filter(
            OpinionRequest.id == opinion_data.opinion_request_id
        ).first()
        
        new_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == "expert_opinion_submitted"
        ).first()
        
        old_status_id = request.current_status_id
        request.current_status_id = new_status.id
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=opinion_data.opinion_request_id,
            action_type="opinion_created",
            action_by=current_user.id,
            from_status_id=old_status_id,
            to_status_id=new_status.id,
            action_details={"opinion_id": opinion.id}
        )
        db.add(history)
        
        db.commit()
        return opinion
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/opinions/{opinion_id}/review", response_model=OpinionInDB)
async def review_opinion(
    *,
    opinion_id: int,
    review: OpinionReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Review an opinion."""
    try:
        opinion = db.query(Opinion).filter(Opinion.id == opinion_id).first()
        if not opinion:
            raise HTTPException(status_code=404, detail="Opinion not found")
            
        # Update opinion status
        opinion.status = 'approved' if review.is_approved else 'rejected'
        opinion.review_comments = review.comments
        opinion.reviewed_by = current_user.id
        
        # Update request status
        request = db.query(OpinionRequest).filter(
            OpinionRequest.id == opinion.opinion_request_id
        ).first()
        
        new_status = db.query(WorkflowStatus).filter(
            WorkflowStatus.name == 'head_approved' if review.is_approved else 'rejected'
        ).first()
        
        old_status_id = request.current_status_id
        request.current_status_id = new_status.id
        
        # Record history
        history = WorkflowHistory(
            opinion_request_id=opinion.opinion_request_id,
            action_type="opinion_reviewed",
            action_by=current_user.id,
            from_status_id=old_status_id,
            to_status_id=new_status.id,
            action_details={
                "opinion_id": opinion_id,
                "approved": review.is_approved,
                "comments": review.comments
            }
        )
        db.add(history)
        
        db.commit()
        return opinion
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# Document Management
@router.post("/requests/{request_id}/documents/", response_model=List[DocumentInDB])
async def upload_documents(
    *,
    request_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload documents for an opinion request."""
    try:
        request = db.query(OpinionRequest).filter(OpinionRequest.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Opinion request not found")
        
        uploaded_documents = []
        upload_dir = f"uploads/opinion_requests/{request_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        for file in files:
            file_path = os.path.join(upload_dir, file.filename)
            with open(file_path, "wb+") as file_object:
                file_object.write(file.file.read())
            
            document = Document(
                opinion_request_id=request_id,
                file_name=file.filename,
                file_path=file_path,
                file_type=file.content_type,
                file_size=os.path.getsize(file_path),
                uploaded_by=current_user.id
            )
            db.add(document)
            uploaded_documents.append(document)
        
        db.commit()
        return uploaded_documents
        
    except Exception as e:
        db.rollback()
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