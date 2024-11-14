# app/api/v1/endpoints/departments.py
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.db.session import get_db
from app.models.department import Department
from app.models.auth import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    Department as DepartmentSchema
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/departments", response_model=List[DepartmentSchema])
async def list_departments(
    skip: int = Query(0, description="Skip number of records"),
    limit: int = Query(100, description="Limit number of records"),
    search: str = Query(None, description="Search in department name or code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all departments"""
    query = db.query(Department)
    
    if search:
        query = query.filter(
            or_(
                Department.name.ilike(f"%{search}%"),
                Department.code.ilike(f"%{search}%")
            )
        )
    
    departments = query.offset(skip).limit(limit).all()
    return departments

@router.post("/departments", response_model=DepartmentSchema)
async def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new department"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if department exists
    db_dept = db.query(Department).filter(
        or_(
            Department.name == department.name,
            Department.code == department.code
        )
    ).first()
    
    if db_dept:
        raise HTTPException(
            status_code=400,
            detail="Department with this name or code already exists"
        )
    
    db_dept = Department(**department.dict())
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept

@router.get("/departments/{department_id}", response_model=DepartmentSchema)
async def get_department(
    department_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific department by ID"""
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return department

@router.put("/departments/{department_id}", response_model=DepartmentSchema)
async def update_department(
    department_update: DepartmentUpdate,
    department_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update department"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    update_data = department_update.dict(exclude_unset=True)
    
    # Check uniqueness if updating name or code
    if "name" in update_data or "code" in update_data:
        existing = db.query(Department).filter(
            or_(
                Department.name == update_data.get("name", department.name),
                Department.code == update_data.get("code", department.code)
            ),
            Department.id != department_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Department with this name or code already exists"
            )
    
    for field, value in update_data.items():
        setattr(department, field, value)
    
    db.commit()
    db.refresh(department)
    return department

@router.delete("/departments/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete department"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if department has users
    if department.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department that has users assigned"
        )
    
    db.delete(department)
    db.commit()
    return None

@router.post("/departments/{department_id}/users/{user_id}", status_code=status.HTTP_200_OK)
async def assign_user_to_department(
    department_id: int = Path(..., gt=0),
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign user to department"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.department_id = department_id
    db.commit()
    
    return {"message": "User assigned to department successfully"}

@router.delete("/departments/{department_id}/users/{user_id}", status_code=status.HTTP_200_OK)
async def remove_user_from_department(
    department_id: int = Path(..., gt=0),
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove user from department"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = db.query(User).filter(
        User.id == user_id,
        User.department_id == department_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in this department"
        )
    
    user.department_id = None
    db.commit()
    
    return {"message": "User removed from department successfully"}