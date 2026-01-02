from pydantic import BaseModel
from datetime import datetime


class AppointmentCreate(BaseModel):
    """Схема для создания записи"""
    salon_id: int
    master_id: int
    service_id: int
    date_time: datetime
    comment: str | None = None


class AppointmentResponse(BaseModel):
    """Схема для ответа с информацией о записи"""
    id: int
    salon_id: int
    master_id: int
    service_id: int
    date_time: datetime
    end_time: datetime
    status: bool
    comment: str | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True

