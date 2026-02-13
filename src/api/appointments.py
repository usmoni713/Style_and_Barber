from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, status

from src.core.security import get_user_from_id
from src.models import users as DBUser
from src.services.user_service import UserService
from src.services.appointment_service import AppointmentService
from src.schemas import User, AppointmentCreate

from .depends_functions import get_user_service, get_appointment_service

router = APIRouter(prefix="/api/v1/users", tags=["appointments"])


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
    from_date: date = None,          # От какой даты (YYYY-MM-DD)
    to_date: date = None,             # До какой даты (YYYY-MM-DD)
    salon_id: int = None,             
    sort_by: str = "date_time",       # Сортировка: date_time, created_at
    order: str = "desc",             # Порядок сортировки: asc или desc
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
    
    appointments = await service.get_user_appointments(user.id, from_date=from_date, to_date=to_date, salon_id=salon_id, sort_by=sort_by, order=order)
    return {"status": "success","data": {"appointments": appointments}}


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

@router.put("/appointments/{appointment_id}")
async def update_appointment(
    appointment_id: int,
    date_time: datetime,
    master_id: int,
    comment: str | None,
    user: DBUser = Depends(get_user_from_id),
    service: AppointmentService = Depends(get_appointment_service)
    ):
    """
    Обновление существующей записи
    
    Args:
        appointment_id: ID записи
        appointment_data: Новые данные записи
        service: Сервис записей
        
    Returns:
        dict: Информация об обновленной записи
    """
    return await service.update_appointment(appointment_id, date_time, master_id, comment, user.id)

@router.delete("/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    reason: str = Query(None, description="Причина удаления записи"),
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
    return await service.delete_appointment(appointment_id, user.id, reason)

