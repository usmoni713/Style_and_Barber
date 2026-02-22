from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# class MasterCreate(BaseModel):
#     """Схема для создание мастера"""
#     user_id: int
#     photo: str
#     specialization: str
#     about: str


class MasterEdit(BaseModel):
    """Схема для редактирования мастера"""
    photo: str
    specialization: str
    about: str


class MasterResponse(BaseModel):
    """Схема ответа с информацией о мастере"""
    id: int
    user_id: int
    photo: str
    specialization: str
    about: str
    rating: float = 0.0
    reviews_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


