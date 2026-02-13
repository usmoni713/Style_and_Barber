from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, status

from src.core.security import get_user_from_id
from src.models import users as DBUser
from src.services.user_service import UserService
from src.services.appointment_service import AppointmentService
from src.schemas import UserEdit, AppointmentCreate

from .depends_functions import get_user_service, get_appointment_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/profile")
async def get_profile(
    user: DBUser = Depends(get_user_from_id),
    service: UserService = Depends(get_user_service)
):
    """
    Получение профиля текущего пользователя
    
    Args:
        user: Текущий пользователь (из JWT токена)
        service: Сервис пользователей (внедряется через DI)
        
    Returns:
        dict: Информация о пользователе
    """

    return await service.get_user_profile(user.id)

@router.put("/profile")
async def update_profile(
    user: DBUser = Depends(get_user_from_id),
    service: UserService = Depends(get_user_service),
    user_data: UserEdit = None
):
    """
    Обновление профиля текущего пользователя
    
    Args:
        user: Текущий пользователь (из JWT токена)
        service: Сервис пользователей (внедряется через DI)
        
    Returns:
        dict: Информация о пользователе
    """
    
    return await service.update_user(user.id, user_data)

