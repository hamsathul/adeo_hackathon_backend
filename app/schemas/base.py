# app/schemas/base.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

class TimestampedBase(BaseModel):
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool = True
    is_superuser: bool = False

    class Config:
        from_attributes = True
        
class DepartmentBase(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True