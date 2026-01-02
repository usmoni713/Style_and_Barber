from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status


from src.models import (admins as DBadmin,
                        admin_salon as DBadmin_salon,
                        )
from src.repository.base_repo import BaseRepository
from src.core.utils import hashing_password
from src.schemas import AdminCreate, SalonEdit, SalonCreate, ServiceCreate, UserEdit, User, AdminEdit, MasterEdit


class AdminService:
    """Сервис для работы с администратором"""

    def __init__(self, session:AsyncSession):
        """
        Инициализация сервиса с сессией БД
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
        self.repo = BaseRepository(DBadmin, session)

    async def create_admin(self, admin_data:AdminCreate ):       
        try:
            new_admin = DBadmin(
                phone = admin_data.phone,
                email = admin_data.email,
                password_hash = await hashing_password(admin_data.password),
                first_name = admin_data.name,
                last_name = admin_data.last_name,
                super_admin = admin_data.super_admin,    
            )
            async with self.session.begin():
                self.session.add(new_admin)
                await self.session.flush()
                admin_salon_objecs: list = []

                for salon_id in admin_data.salons_id:
                    admin_salon_objecs.append(DBadmin_salon(salon_id=salon_id, admin_id=new_admin.id))
                self.session.add_all(admin_salon_objecs)
    
                return {
                    "message": "Admin created successfully",
                    "admin": {
                        "id": new_admin.id,
                        "phone": admin_data.phone,
                        "email": admin_data.email,
                        "first_name": admin_data.name,
                        "last_name": admin_data.last_name,
                        "super_admin": admin_data.super_admin,
                        "salons": [admin_data.salons_id]
                    }
                }
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email or phone number is already busy."
            )

    async def delete_admin(self, admin_id:int):
        async with self.session.begin():
            stmt_check = select(DBadmin).where(DBadmin.id == admin_id)
            result_check = await self.session.execute(stmt_check)
            admin_to_delete = result_check.scalar_one_or_none()
            
            if not admin_to_delete:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found"
                )
            
            if not admin_to_delete.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Admin has already been deleted"
                )
            admin_to_delete.is_active = False
            
            return {"message": f"Admin {admin_id} deleted successfully"}

    async def update_admin(self, admin_id: int, admin_data: AdminEdit) -> dict:
        """Обновление администратора"""
        from src.models import salons as DBsalon
        
        async with self.session.begin():
            stmt = select(DBadmin).options(selectinload(DBadmin.salons)).where(DBadmin.id == admin_id)
            result = await self.session.execute(stmt)
            admin_to_update = result.scalar_one_or_none()
            
            if not admin_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found"
                )
            
            if admin_data.email != admin_to_update.email:
                stmt_check = select(DBadmin).where(
                    and_(DBadmin.email == admin_data.email, DBadmin.id != admin_id)
                )
                result_check = await self.session.execute(stmt_check)
                if result_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Admin with this email already exists"
                    )
            
            if admin_data.phone and admin_data.phone != admin_to_update.phone:
                stmt_check = (select(DBadmin).where(and_(DBadmin.phone == admin_data.phone, DBadmin.id != admin_id)))
                result_check = await self.session.execute(stmt_check)
                if result_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Admin with this phone already exists"
                    )
            
            admin_to_update.first_name = admin_data.first_name
            admin_to_update.last_name = admin_data.last_name
            admin_to_update.email = admin_data.email
            admin_to_update.phone = admin_data.phone
            admin_to_update.super_admin = admin_data.super_admin
            
            stmt_salons = select(DBsalon).where(DBsalon.id.in_(admin_data.salons_id))
            result_salons = await self.session.execute(stmt_salons)
            salons = result_salons.scalars().all()
            admin_to_update.salons = salons
            
            return {
                "message": "Admin updated successfully",
                "admin": {
                    "id": admin_to_update.id,
                    "first_name": admin_to_update.first_name,
                    "last_name": admin_to_update.last_name,
                    "email": admin_to_update.email,
                    "phone": admin_to_update.phone,
                    "super_admin": admin_to_update.super_admin,
                    "salons": [salon.id for salon in salons]
                }
            }

    async def get_all_admins(self) -> list[dict]:
        """Получение списка всех администраторов"""
        from src.models import salons as DBsalon
        
        stmt = select(DBadmin).where(DBadmin.is_active == True)
        result = await self.session.execute(stmt)
        admins = result.scalars().all()
        
        admins_list = []
        for admin_item in admins:
            salons_stmt = select(DBsalon).join(
                DBadmin_salon, DBsalon.id == DBadmin_salon.salon_id
            ).where(DBadmin_salon.admin_id == admin_item.id)
            salons_result = await self.session.execute(salons_stmt)
            salons = salons_result.scalars().all()
            
            admins_list.append({
                "id": admin_item.id,
                "first_name": admin_item.first_name,
                "last_name": admin_item.last_name,
                "email": admin_item.email,
                "phone": admin_item.phone,
                "super_admin": admin_item.super_admin,
                "salons": [salon.id for salon in salons]
            })
        return admins_list

    async def get_salon_admins(self, salon_id: int) -> list[dict]:
        """Получение списка администраторов конкретного салона"""
        from src.models import salons as DBsalon
        
        salon_stmt = select(DBsalon).where(DBsalon.id == salon_id)
        salon_result = await self.session.execute(salon_stmt)
        salon = salon_result.scalar_one_or_none()
        
        if not salon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Salon not found"
            )
        
        stmt = (
            select(DBadmin)
            .join(DBadmin_salon, DBadmin.id == DBadmin_salon.admin_id)
            .where(
                and_(
                    DBadmin_salon.salon_id == salon_id,
                    DBadmin.is_active == True
                )
            )
        )
        result = await self.session.execute(stmt)
        admins = result.scalars().all()
        
        admins_list = []
        for admin_item in admins:
            admins_list.append({
                "id": admin_item.id,
                "first_name": admin_item.first_name,
                "last_name": admin_item.last_name,
                "email": admin_item.email,
                "phone": admin_item.phone,
                "super_admin": admin_item.super_admin
            })
        return admins_list







