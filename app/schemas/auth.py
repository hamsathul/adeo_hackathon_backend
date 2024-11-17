# app/schemas/auth.py
from typing import ForwardRef, List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.schemas.department import Department

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

# User models
class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class User(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    roles: List[Role] = []
    department_id: Optional[int] = None
    department: Optional[Department] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
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
        populate_by_name = True
        arbitrary_types_allowed = True

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
        populate_by_name = True
        arbitrary_types_allowed = True

# Login models
class LoginRequest(BaseModel):
    username: str
    password: str

# New models for CRUD operations
class UserList(BaseModel):
    total: int
    items: List[User]
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    success: bool
    message: str
    data: Optional[User] = None

class UserSearchParams(BaseModel):
    skip: int = 0
    limit: int = 100
    search: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role: Optional[str] = None

# Resolve forward references for Pydantic models
User.model_rebuild()
Role.model_rebuild()
Permission.model_rebuild()