from pydantic import BaseModel, EmailStr
from datetime import datetime




class AdminCreate(BaseModel):   
    """
    Схема для создание администратора
    """
    phone: str | None = None
    email: EmailStr
    password: str
    name: str
    last_name: str|None = None
    super_admin : bool = False
    salons_id: list[int] 


class AdminEdit(BaseModel):
    """Схема для редактирования администратора"""
    first_name: str
    last_name: str | None = None
    email: EmailStr
    phone: str | None = None
    super_admin: bool = False
    salons_id: list[int]


