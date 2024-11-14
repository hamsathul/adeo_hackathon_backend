# app/api/v1/endpoints/roles.py
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.db.session import get_db
from app.models.auth import User, Role, Permission
from app.schemas.auth import (
    RoleCreate, Role as RoleSchema, Permission as PermissionSchema
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/roles", response_model=List[RoleSchema])
async def list_roles(
    skip: int = Query(0, description="Skip number of records"),
    limit: int = Query(100, description="Limit number of records"),
    search: str = Query(None, description="Search in role name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all roles"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    query = db.query(Role)
    
    if search:
        query = query.filter(Role.name.ilike(f"%{search}%"))
    
    roles = query.offset(skip).limit(limit).all()
    return roles

@router.post("/roles", response_model=RoleSchema)
async def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new role"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if role exists
    db_role = db.query(Role).filter(Role.name == role.name).first()
    if db_role:
        raise HTTPException(
            status_code=400,
            detail="Role with this name already exists"
        )
    
    # Create role
    db_role = Role(
        name=role.name,
        description=role.description
    )
    
    # Add permissions
    if role.permissions:
        permissions = db.query(Permission).filter(
            Permission.name.in_(role.permissions)
        ).all()
        
        if len(permissions) != len(role.permissions):
            raise HTTPException(
                status_code=400,
                detail="Some permissions do not exist"
            )
        
        db_role.permissions = permissions
    
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

@router.get("/roles/{role_id}", response_model=RoleSchema)
async def get_role(
    role_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific role by ID"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return role

@router.put("/roles/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: int = Path(..., gt=0),
    role_update: RoleCreate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update role"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get role
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if not db_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check name uniqueness if changing name
    if role_update.name != db_role.name:
        existing_role = db.query(Role).filter(Role.name == role_update.name).first()
        if existing_role:
            raise HTTPException(
                status_code=400,
                detail="Role with this name already exists"
            )
    
    # Update basic fields
    db_role.name = role_update.name
    db_role.description = role_update.description
    
    # Update permissions
    if role_update.permissions:
        permissions = db.query(Permission).filter(
            Permission.name.in_(role_update.permissions)
        ).all()
        
        if len(permissions) != len(role_update.permissions):
            raise HTTPException(
                status_code=400,
                detail="Some permissions do not exist"
            )
        
        db_role.permissions = permissions
    
    db.commit()
    db.refresh(db_role)
    return db_role

@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete role"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if role is assigned to users
    if role.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role that is assigned to users"
        )
    
    db.delete(role)
    db.commit()
    return None

@router.post("/roles/{role_id}/users/{user_id}", status_code=status.HTTP_200_OK)
async def assign_role_to_user(
    role_id: int = Path(..., gt=0),
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign role to user"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get role and user
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user already has this role
    if role in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has this role"
        )
    
    # Assign role
    user.roles.append(role)
    db.commit()
    
    return {"message": "Role assigned successfully"}

@router.delete("/roles/{role_id}/users/{user_id}", status_code=status.HTTP_200_OK)
async def remove_role_from_user(
    role_id: int = Path(..., gt=0),
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove role from user"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get role and user
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has this role
    if role not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User doesn't have this role"
        )
    
    # Remove role
    user.roles.remove(role)
    db.commit()
    
    return {"message": "Role removed successfully"}