from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.base import UserBase, DepartmentBase
from app.schemas.opinion import (
    OpinionRequestInDB,
    OpinionInDB
)

class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_active: bool = True

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Department(DepartmentBase):
    users: List[UserBase] = []
    opinion_requests: List[OpinionRequestInDB] = []
    opinions: List[OpinionInDB] = []

    class Config:
        from_attributes = True

class DepartmentList(BaseModel):
    total: int
    items: List[Department]

    class Config:
        from_attributes = True
