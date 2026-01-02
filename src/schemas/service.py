from pydantic import BaseModel, EmailStr
from datetime import datetime


class ServiceCreate(BaseModel):
    """Схема для создания услуги"""
    description: str
    duration_minutes: int
    base_price: int


class ServiceEdit(BaseModel):
    """Схема для редактирования услуги"""
    id: int
    description: str
    duration_minutes: int
    base_price: int



