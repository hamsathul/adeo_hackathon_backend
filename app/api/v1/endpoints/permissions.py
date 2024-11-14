# app/api/v1/endpoints/permissions.py
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from app.db.session import get_db
from app.models.auth import User, Role, Permission
from app.schemas.auth import (
    Permission as PermissionSchema,
    PermissionCreate,
    Role as RoleSchema
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()

@router.get("/permissions", response_model=List[PermissionSchema])
async def list_permissions(
    skip: int = Query(0, description="Skip number of records"),
    limit: int = Query(100, description="Limit number of records"),
    search: str = Query(None, description="Search in permission name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all permissions"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    query = db.query(Permission)
    
    if search:
        query = query.filter(
            or_(
                Permission.name.ilike(f"%{search}%"),
                Permission.description.ilike(f"%{search}%")
            )
        )
    
    permissions = query.offset(skip).limit(limit).all()
    return permissions

@router.post("/permissions", response_model=PermissionSchema)
async def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new permission"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if permission exists
    db_permission = db.query(Permission).filter(
        Permission.name == permission.name
    ).first()
    if db_permission:
        raise HTTPException(
            status_code=400,
            detail="Permission with this name already exists"
        )
    
    # Create permission
    db_permission = Permission(
        name=permission.name,
        description=permission.description
    )
    
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission

@router.get("/permissions/{permission_id}", response_model=PermissionSchema)
async def get_permission(
    permission_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific permission by ID"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    return permission

@router.put("/permissions/{permission_id}", response_model=PermissionSchema)
async def update_permission(
    permission_update: PermissionCreate,
    permission_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update permission"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get permission
    db_permission = db.query(Permission).filter(
        Permission.id == permission_id
    ).first()
    if not db_permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Check name uniqueness if changing name
    if permission_update.name != db_permission.name:
        existing = db.query(Permission).filter(
            Permission.name == permission_update.name
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Permission with this name already exists"
            )
    
    # Update fields
    db_permission.name = permission_update.name
    db_permission.description = permission_update.description
    
    db.commit()
    db.refresh(db_permission)
    return db_permission

@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(
    permission_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete permission"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Check if permission is assigned to roles
    if permission.roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete permission that is assigned to roles"
        )
    
    db.delete(permission)
    db.commit()
    return None

@router.get("/permissions/{permission_id}/roles", response_model=List[RoleSchema])
async def get_roles_with_permission(
    permission_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all roles that have this permission"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    return permission.roles

