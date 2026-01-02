from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.services.auth_service import AuthService

from .depends_functions import get_auth_service

router = APIRouter(tags=["auth"])


@router.post("/signin")
async def signin_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """
    Авторизация пользователя
    
    Args:
        form_data: Форма с username (email/phone) и password
        service: Сервис авторизации
        
    Returns:
        dict: JWT токен
    """
    return await service.authenticate_user(form_data)


@router.post("/admin/signin")
async def signin_admin(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """
    Авторизация админа
    
    Args:
        form_data: Форма с username (email/phone) и password
        service: Сервис авторизации
        
    Returns:
        dict: JWT токен
    """
    return await service.authenticate_admin(form_data)


