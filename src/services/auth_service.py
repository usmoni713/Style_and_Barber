from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.models import users as DBUser, admins as DBadmin
from src.core.security import create_jwt_token
from src.core.utils import verify_password


class AuthService:
    """Сервис для авторизации"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def authenticate_user(
        self, 
        form_data: OAuth2PasswordRequestForm
    ) -> dict:
        """
        Авторизация пользователя
        
        Args:
            form_data: Данные формы (username может быть email или phone)
            
        Returns:
            dict: JWT токен
        """
        login_value = form_data.username
        
        stmt = select(DBUser).where(
            or_(
                DBUser.email == login_value,
                DBUser.phone == login_value
            )
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        password_valid = await verify_password(
            password=form_data.password,
            hashed=user.password_hash
        )
        
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        token = await create_jwt_token({"user_id": user.id})
        
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    
    async def authenticate_admin(
        self,
        form_data: OAuth2PasswordRequestForm
    ) -> dict:
        """Авторизация администратора"""
        login_value = form_data.username
        
        stmt = select(DBadmin).where(
            or_(
                DBadmin.email == login_value,
                DBadmin.phone == login_value
            )
        )
        result = await self.session.execute(stmt)
        admin = result.scalar_one_or_none()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        password_valid = await verify_password(
            password=form_data.password,
            hashed=admin.password_hash
        )
        
        if not password_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        
        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been banned"
            )
        
        token = await create_jwt_token({"admin_id": admin.id})
        
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    
    