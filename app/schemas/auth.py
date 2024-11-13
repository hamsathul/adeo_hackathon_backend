from typing import ForwardRef, List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

Role = ForwardRef('Role')
Permission = ForwardRef('Permission')

# Token models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []

class UserBase(BaseModel):
    email: EmailStr
    username: str
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    roles: List[Role] = []  # ForwardRef to Role

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    permissions: List[str] = []

class Role(RoleBase):
    id: int
    created_at: datetime
    permissions: List[Permission] = []  # ForwardRef to Permission

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

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

class LoginRequest(BaseModel):
    username: str
    password: str

# Resolve forward references for Pydantic models
User.model_rebuild()
Role.model_rebuild()
Permission.model_rebuild()
