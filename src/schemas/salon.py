from pydantic import BaseModel, EmailStr
from datetime import datetime


class SalonCreate(BaseModel):
    """Схема для создания салона"""
    title: str
    address: str
    phone: str
    photo_url: str


class SalonEdit(BaseModel):
    """Схема для редактирования салона"""
    id: int
    title: str
    address: str
    phone: str
    photo_url: str


class SalonResponse(BaseModel):
    """Схема ответа с информацией о салоне"""
    id: int
    title: str
    address: str
    phone: str
    photo_url: str
    rating: float = 0.0
    reviews_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True




