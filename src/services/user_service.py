from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.models import users as DBUser
from src.repository.base_repo import BaseRepository
from src.core.utils import hashing_password
from src.schemas import User  


class UserService:
    """Сервис для работы с пользователями"""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией БД
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
        self.repo = BaseRepository(DBUser, session)
    
    async def create_user(self, user_data: User) -> dict:
        """
        Создание нового пользователя
        
        Args:
            user_data: Pydantic модель с данными пользователя
            
        Returns:
            dict: Сообщение об успехе
            
        Raises:
            HTTPException: Если email/phone уже заняты
        """
        try:            
            hashed_password = await hashing_password(user_data.password)
            new_user = DBUser(
                first_name=user_data.name,
                last_name=user_data.lastname,
                email=user_data.email,
                phone=user_data.phone,
                password_hash=hashed_password
            )
            async with self.session.begin():
                self.session.add(new_user)
                await self.session.flush()
            
            return {"message": "User created successfully"}
            
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email or phone number is already busy."
            )
    
    async def get_user_appointments(self, user_id: int) -> list[dict]:
        """
        Получение всех записей пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            list[dict]: Список записей
        """
        from src.models import appointments as DBappointment
        from sqlalchemy import select, and_
        
        async with self.session:
            stmt = select(DBappointment).where(
                and_(
                    DBappointment.client_id == user_id,
                    DBappointment.is_active == True
                )
            )
            result = await self.session.execute(stmt)
            appointments = result.scalars().all()
            
            appointments_list = []
            for apt in appointments:
                appointments_list.append({
                    "id": apt.id,
                    "salon_id": apt.salon_id,
                    "master_id": apt.master_id,
                    "service_id": apt.service_id,
                    "date_time": apt.date_time.isoformat() if apt.date_time else None,
                    "end_time": apt.end_time.isoformat() if apt.end_time else None,
                    "status": apt.status,
                    "comment": apt.comment,
                    "created_at": apt.created_at.isoformat() if apt.created_at else None
                })
            
            return appointments_list

    async def update_user(self, user_id: int, user_data) -> dict:
        """Обновление пользователя (для суперадмина)"""
        from sqlalchemy import select, and_
        from src.schemas import UserEdit
        
        async with self.session.begin():
            stmt = select(DBUser).where(DBUser.id == user_id)
            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if user_data.email != user.email:
                stmt_check = select(DBUser).where(
                    and_(DBUser.email == user_data.email, DBUser.id != user_id)
                )
                result_check = await self.session.execute(stmt_check)
                if result_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User with this email already exists"
                    )
            
            if user_data.phone and user_data.phone != user.phone:
                stmt_check = select(DBUser).where(
                    and_(DBUser.phone == user_data.phone, DBUser.id != user_id)
                )
                result_check = await self.session.execute(stmt_check)
                if result_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User with this phone already exists"
                    )
            
            user.first_name = user_data.first_name
            user.last_name = user_data.last_name
            user.email = user_data.email
            user.phone = user_data.phone
            
            return {
                "message": "User updated successfully",
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone
                }
            }

    async def delete_user(self, user_id: int) -> dict:
        """Удаление пользователя (soft delete)"""
        from sqlalchemy import select, and_, update
        
        async with self.session.begin():
            stmt_check = select(DBUser).where(DBUser.id == user_id)
            result_check = await self.session.execute(stmt_check)
            user_to_delete = result_check.scalar_one_or_none()
            
            if not user_to_delete:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user_to_delete.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="User has already been deleted"
                )
            
            user_to_delete.is_active = False
            
            return {"message": f"User {user_id} deleted successfully"}

    async def get_all_users(self) -> list[dict]:
        """Получение списка всех пользователей"""
        from sqlalchemy import select
        
        stmt = select(DBUser).where(DBUser.is_active == True)
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        users_list = []
        for user in users:
            users_list.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone
            })
        return users_list

    async def get_salon_users(self, salon_id: int) -> list[dict]:
        """Получение списка пользователей с записями в конкретном салоне"""
        from sqlalchemy import select, and_, distinct
        from src.models import appointments as DBappointment
        
        stmt = (
            select(DBUser)
            .join(DBappointment, DBUser.id == DBappointment.client_id)
            .where(
                and_(
                    DBappointment.salon_id == salon_id,
                    DBUser.is_active == True
                )
            )
            .distinct()
        )
        result = await self.session.execute(stmt)
        users = result.scalars().all()
        
        users_list = []
        for user in users:
            users_list.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone
            })
        return users_list
        
        