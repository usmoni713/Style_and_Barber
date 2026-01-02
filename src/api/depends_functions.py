from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.salon_service import SalonService
from src.services.admin_service import AdminService
from src.services.auth_service import AuthService
from src.services.user_service import UserService
from src.services.appointment_service import AppointmentService
from src.services.service_service import ServiceService
from src.services.master_service import MasterService

from src.core.database import get_db_session



async def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    """Создание сервиса пользователей"""
    return UserService(session)


async def get_appointment_service(session: AsyncSession = Depends(get_db_session)) -> AppointmentService:
    """Создание сервиса записей"""
    return AppointmentService(session)



async def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    """Создание сервиса авторизации"""
    return AuthService(session)


async def get_admin_service(session: AsyncSession = Depends(get_db_session)) -> AdminService:
    return AdminService(session)


async def get_salon_service(session: AsyncSession = Depends(get_db_session)) -> SalonService:
    """Создание сервиса салонов"""
    return SalonService(session)


async def get_service_service(session: AsyncSession = Depends(get_db_session)) -> ServiceService:
    """Создание сервиса услуг"""
    return ServiceService(session)


async def get_master_service(session: AsyncSession = Depends(get_db_session)) -> MasterService:
    """Создание сервиса мастеров"""
    return MasterService(session)

