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




