from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.schemas import SalonEdit
from src.models import (salons as DBsalon,
                        masters as DBmaster,
                        master_salon as DBmaster_salon,
                        services as DBservice,
                        admin_salon as DBadmin_salon,
                        admins as DBadmin

) 
from src.repository.base_repo import BaseRepository

from sqlalchemy.orm import selectinload



class SalonService:
    """Сервис для работы с салонами"""
    
    def __init__(self, session: AsyncSession):
        """
        Инициализация сервиса с сессией БД
        
        Args:
            session: Асинхронная сессия SQLAlchemy
        """
        self.session = session
        self.repo = BaseRepository(DBsalon, session)

    async def get_all_salons(self, only_active: bool = True):
        if only_active:
            stmt = select(DBsalon).where(DBsalon.is_active == True)
            result = await self.session.execute(stmt)
            salons_ls = result.scalars().all()
        else: 
            salons_ls = await self.repo.get_all()
        salons_list = []
        for salon in salons_ls:
            salons_list.append({
                "id": salon.id,
                "title": salon.title,
                "address": salon.address,
                "phone": salon.phone,
                "photo_url": salon.photo_url
            })
        return salons_list
    
    async def get_masters(self, salon_id:int | None = None, service_id:int | None = None):
        from src.models import master_service as DBmaster_service
        
        if salon_id and service_id:
            stmt = (
                select(DBmaster)
                .join(DBmaster_salon, DBmaster.id == DBmaster_salon.master_id)
                .join(DBmaster_service, DBmaster.id == DBmaster_service.master_id)
                .where(
                    and_(
                        DBmaster.is_active == True,
                        DBmaster_salon.salon_id == salon_id,
                        DBmaster_service.service_id == service_id
                    )
                )
            )
        elif salon_id:
            stmt = (
                select(DBmaster)
                .join(DBmaster_salon, DBmaster.id == DBmaster_salon.master_id)
                .where(
                    and_(
                        DBmaster.is_active == True,
                        DBmaster_salon.salon_id == salon_id
                    )
                )
            )
        elif service_id:
            stmt = (
                select(DBmaster)
                .join(DBmaster_service, DBmaster.id == DBmaster_service.master_id)
                .where(
                    and_(
                        DBmaster.is_active == True,
                        DBmaster_service.service_id == service_id
                    )
                )
            )
        else:
            stmt = select(DBmaster).where(DBmaster.is_active == True)
        
        result = await self.session.execute(stmt)
        masters = result.scalars().all()
        
        masters_list = []
        for master in masters:
            masters_list.append({
                "id": master.id,
                "photo": master.photo,
                "specialization": master.specialization,
                "about": master.about,
                "user_id": master.user_id
            })
        return masters_list

    async def get_services(self):
            stmt = select(DBservice).where(DBservice.is_active == True)
            result = await self.session.execute(stmt)
            services = result.scalars().all()
            
            services_list = []
            for service in services:
                services_list.append({
                    "id": service.id,
                    "description": service.description,
                    "duration_minutes": service.duration_minutes,
                    "base_price": service.base_price
                })
        
            return services_list

    async def get_salon_for_admin(self, admin_id:int, salon_id:int, dowload_apponimens:bool = False, dowload_masters:bool = False ):
        stmt = (
        select(DBsalon)
        .join(DBadmin_salon, DBsalon.id == DBadmin_salon.salon_id).join(DBadmin, DBadmin_salon.admin_id==DBadmin.id)
        .where(
            and_(
                DBadmin.is_active == True,
                DBadmin_salon.salon_id == salon_id,
                DBadmin_salon.admin_id == admin_id
            )
        )
        )
        if dowload_apponimens: 
            stmt = (
                select(DBsalon)
                .options(selectinload(DBsalon.appointments))
                .join(DBadmin_salon, DBsalon.id == DBadmin_salon.salon_id)
                .join(DBadmin, DBadmin_salon.admin_id == DBadmin.id)
                .where(
                    and_(
                        DBadmin.is_active == True,
                        DBadmin_salon.salon_id == salon_id,
                        DBadmin_salon.admin_id == admin_id
                    )
                )
            )
        elif dowload_masters:
                stmt = (
                select(DBsalon)
                .options(selectinload(DBsalon.masters))
                .join(DBadmin_salon, DBsalon.id == DBadmin_salon.salon_id)
                .join(DBadmin, DBadmin_salon.admin_id == DBadmin.id)
                .where(
                    and_(
                        DBadmin.is_active == True,
                        DBadmin_salon.salon_id == salon_id,
                        DBadmin_salon.admin_id == admin_id
                    )
                )
            )

        result = await self.session.execute(stmt)
        salon = result.scalar_one_or_none()
        if not salon:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="you do not have access to this salon.")
        return salon

    async def get_all_salons_for_admin(self, admin_id:int):
        stmt = (select(DBsalon)
                .join(DBadmin_salon, DBsalon.id == DBadmin_salon.salon_id)
                .where(DBadmin_salon.admin_id == admin_id)
        )
        result = await self.session.execute(stmt)
        salons_ls = result.scalars().all()
        salons_list = []
        for salon in salons_ls:
            salons_list.append({
                "id": salon.id,
                "title": salon.title,
                "address": salon.address,
                "phone": salon.phone,
                "photo_url": salon.photo_url
            })
        return salons_list

    async def edit_salon(self, salon_data:SalonEdit, admin_id:int):
        async with self.session.begin():
            salon = await self.get_salon_for_admin(admin_id=admin_id, salon_id=salon_data.id)
            salon.title = salon_data.title
            salon.address = salon_data.address
            salon.phone = salon_data.phone
            salon.photo_url = salon_data.photo_url    

            return {"message":"edited successfully"}

    async def create_salon(self, salon_data) -> dict:
        """Создание нового салона (для суперадмина)"""
        from src.schemas import SalonCreate
        
        async with self.session.begin():
            new_salon = DBsalon(
                title=salon_data.title,
                address=salon_data.address,
                phone=salon_data.phone,
                photo_url=salon_data.photo_url
            )
            self.session.add(new_salon)
            await self.session.flush()
            
            return {
                "message": "Salon created successfully",
                "salon": {
                    "id": new_salon.id,
                    "title": new_salon.title,
                    "address": new_salon.address,
                    "phone": new_salon.phone,
                    "photo_url": new_salon.photo_url
                }
            }

    async def update_salon(self, salon_id: int, salon_data) -> dict:
        """Обновление салона (для суперадмина)"""
        from src.schemas import SalonCreate
        
        async with self.session.begin():
            stmt = select(DBsalon).where(DBsalon.id == salon_id)
            result = await self.session.execute(stmt)
            salon = result.scalar_one_or_none()
            
            if not salon:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Salon not found"
                )
            
            salon.title = salon_data.title
            salon.address = salon_data.address
            salon.phone = salon_data.phone
            salon.photo_url = salon_data.photo_url
            
            return {
                "message": "Salon updated successfully",
                "salon": {
                    "id": salon.id,
                    "title": salon.title,
                    "address": salon.address,
                    "phone": salon.phone,
                    "photo_url": salon.photo_url
                }
            }

    async def delete_master_from_salon(self, salon_id: int, master_id: int, admin_id: int) -> dict:
        """Удаление мастера из салона"""
        from sqlalchemy import delete
        
        async with self.session.begin():
            salon = await self.get_salon_for_admin(admin_id=admin_id, salon_id=salon_id)
            
            stmt = delete(DBmaster_salon).where(
                and_(
                    DBmaster_salon.salon_id == salon.id,
                    DBmaster_salon.master_id == master_id
                )
            )
            await self.session.execute(stmt)
            
            return {"message": f"Master {master_id} deleted from salon {salon_id}"}

    async def add_master_to_salon(self, salon_id: int, master_email: str, admin_id: int) -> dict:
        """Добавление мастера в салон"""
        from src.models import users as DBUser
        from sqlalchemy.orm import selectinload
        
        async with self.session.begin():
            salon = await self.get_salon_for_admin(
                admin_id=admin_id,
                salon_id=salon_id,
                dowload_masters=True
            )
            
            stmt_user = select(DBUser).options(
                selectinload(DBUser.master)
            ).where(DBUser.email == master_email)
            result_user = await self.session.execute(stmt_user)
            dbuser = result_user.scalar_one_or_none()
            
            if not dbuser:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with email {master_email} not found"
                )
            
            if not dbuser.master:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"User {master_email} is not a master"
                )
            
            dbmaster = dbuser.master[0]
            
            if dbmaster in salon.masters:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Master {dbmaster.id} is already added to this salon"
                )
            
            salon.masters.append(dbmaster)
            
            return {"message": f"Master {dbmaster.id} successfully added to salon {salon_id}"}

    async def get_appointments_for_salon(self, salon_id: int, admin_id: int) -> list[dict]:
        """Получение всех записей салона"""
        async with self.session.begin():
            salon = await self.get_salon_for_admin(
                admin_id=admin_id,
                salon_id=salon_id,
                dowload_apponimens=True
            )
            appointments = salon.appointments
            
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
                    "created_at": apt.created_at.isoformat() if apt.created_at else None,
                    "is_active": apt.is_active
                })
            return appointments_list

    async def delete_appointment_for_salon(
        self,
        salon_id: int,
        appointment_id: int,
        admin_id: int
    ) -> dict:
        """Удаление записи в салоне"""
        from src.models import appointments as DBappointment
        from sqlalchemy import update
        
        async with self.session.begin():
            salon = await self.get_salon_for_admin(admin_id=admin_id, salon_id=salon_id)
            
            stmt_check = select(DBappointment).where(
                and_(
                    DBappointment.id == appointment_id,
                    DBappointment.salon_id == salon_id
                )
            )
            result_check = await self.session.execute(stmt_check)
            appointment = result_check.scalar_one_or_none()
            
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found"
                )
            
            if not appointment.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Appointment has already been deleted"
                )
            
            appointment.is_active = False
            
            return {"message": f"Appointment {appointment_id} deleted successfully"}
