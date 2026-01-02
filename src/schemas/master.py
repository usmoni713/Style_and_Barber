from pydantic import BaseModel, EmailStr
from datetime import datetime


# class MasterCreate(BaseModel):
#     """Схема для создание мастера"""
#     user_id: int
#     photo: str
#     specialization: str
#     about: str
# TODO добавить схему для создание мастера и редактирование сервисов мастера
    

class MasterEdit(BaseModel):
    """Схема для редактирования мастера"""
    photo: str
    specialization: str
    about: str


