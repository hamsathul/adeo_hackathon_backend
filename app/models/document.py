# app/models/document.py
from sqlalchemy import Column, Integer, Text
from sqlalchemy.types import UserDefinedType
from app.db.base import Base

class Vector(UserDefinedType):
    def get_col_spec(self):
        return "VECTOR(1536)"

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    embedding = Column(Vector)  # Use custom Vector type
