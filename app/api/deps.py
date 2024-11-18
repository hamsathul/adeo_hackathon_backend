#app/api/deps.py

# app/api/deps.py

from typing import Generator, List
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import (
    get_current_user,
    get_current_active_user,
    check_permissions
)
from app.models.auth import User

def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current admin user
    """
    admin_roles = {"admin", "superadmin"}  # Add your admin role names
    user_roles = {role.name for role in current_user.roles}
    
    if not any(role in admin_roles for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_department_head(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current department head user
    """
    if not any(role.name == "department_head" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be a department head"
        )
    return current_user

def get_current_expert(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current expert user
    """
    if not any(role.name == "expert" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User must be an expert"
        )
    return current_user

def check_department_access(
    department_id: int,
    current_user: User = Depends(get_current_active_user)
) -> bool:
    """
    Check if user has access to department
    """
    if any(role.name == "admin" for role in current_user.roles):
        return True
    
    if current_user.department_id != department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No permission to access this department"
        )
    return True

# Opinion specific permissions
def can_create_opinion_request(
    current_user: User = Depends(get_current_active_user)
) -> User:
    return check_permissions(["create_opinion_request"])(current_user)

def can_review_opinion(
    current_user: User = Depends(get_current_active_user)
) -> User:
    return check_permissions(["review_opinion"])(current_user)

def can_assign_request(
    current_user: User = Depends(get_current_active_user)
) -> User:
    return check_permissions(["assign_request"])(current_user)

# Utility functions
def validate_pagination(
    skip: int = 0,
    limit: int = 100
) -> tuple:
    """
    Validate pagination parameters
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip value must be non-negative"
        )
    
    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be positive"
        )
    
    if limit > 100:
        limit = 100  # Maximum limit
    
    return skip, limit