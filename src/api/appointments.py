from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.security import get_user_from_id
from src.models import users as DBUser
from src.services.user_service import UserService
from src.services.appointment_service import AppointmentService
from src.schemas import User, AppointmentCreate

from .depends_functions import get_user_service, get_appointment_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])



@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: User,
    service: UserService = Depends(get_user_service)
):
    """
    Регистрация нового пользователя
    
    Args:
        user_data: Данные пользователя
        service: Сервис пользователей (внедряется через DI)
        
    Returns:
        dict: Сообщение об успехе
    """
    return await service.create_user(user_data)


@router.get("/appointments")
async def get_my_appointments(
    user: DBUser = Depends(get_user_from_id),
    service: UserService = Depends(get_user_service)
):
    """
    Получение всех записей текущего пользователя
    
    Args:
        user: Текущий пользователь (из JWT токена)
        service: Сервис пользователей (внедряется через DI)
        
    Returns:
        dict: Список записей
    """
    appointments = await service.get_user_appointments(user.id)
    return {"appointments": appointments}


@router.post("/appointments", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    user: DBUser = Depends(get_user_from_id),
    service: AppointmentService = Depends(get_appointment_service)
):
    """
    Создание новой записи
    
    Args:
        appointment_data: Данные записи
        user: Текущий пользователь
        service: Сервис записей
        
    Returns:
        dict: Информация о созданной записи
    """
    return await service.create_appointment(appointment_data, user.id)


@router.delete("/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    user: DBUser = Depends(get_user_from_id),
    service: AppointmentService = Depends(get_appointment_service)
):
    """
    Удаление записи
    
    Args:
        appointment_id: ID записи
        user: Текущий пользователь
        service: Сервис записей
        
    Returns:
        dict: Сообщение об успехе
    """
    return await service.delete_appointment(appointment_id, user.id)