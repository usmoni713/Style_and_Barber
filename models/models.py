from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    
    name: str
    lastname: str|None = None
    password: str
    email: EmailStr
    phone: str | None = None


class UserLogin(BaseModel):
    login:EmailStr | str
    # email or phone
    password:str


class AppointmentCreate(BaseModel):
    """Модель для создания записи"""
    salon_id: int
    master_id: int
    service_id: int
    date_time: datetime  # Формат: "2025-12-15T14:30:00"
    comment: Optional[str] = None


class AppointmentResponse(BaseModel):
    """Модель для ответа с информацией о записи"""
    id: int
    salon_id: int
    master_id: int
    service_id: int
    date_time: datetime
    end_time: datetime
    status: bool
    comment: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Admin(BaseModel):   
    phone: str | None = None
    email: EmailStr
    password: str
    name: str
    last_name: str|None = None
    super_admin : bool = False
    salons_id: list[int] 



class SalonEdit(BaseModel):
    id: int
    title: str
    address: str
    phone: str
    photo_url: str

