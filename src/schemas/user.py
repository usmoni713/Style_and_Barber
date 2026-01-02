from pydantic import BaseModel, EmailStr


class User(BaseModel):
    """Схема для создания пользователя"""
    name: str
    lastname: str | None = None
    password: str
    email: EmailStr
    phone: str | None = None


class UserEdit(BaseModel):
    """Схема для редактирования пользователя"""
    first_name: str
    last_name: str | None = None
    email: EmailStr
    phone: str | None = None

class UserLogin(BaseModel):
    """
    Схема для авторизации пользователя
    """
    login:EmailStr | str
    # email or phone
    password:str

