from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, date, time, timedelta
from fastapi import HTTPException, status

from src.models import (
    appointments as DBappointment,
    salons as DBsalon,
    masters as DBmaster,
    services as DBservice,
    master_salon as DBmaster_salon
)
from src.schemas import AppointmentCreate


class AppointmentService:
    """Сервис для работы с записями"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_appointment(
        self, 
        appointment_data: AppointmentCreate, 
        user_id: int
    ) -> dict:
        """
        Создание новой записи
        
        Args:
            appointment_data: Данные записи
            user_id: ID пользователя, создающего запись
            
        Returns:
            dict: Информация о созданной записи
        """
        async with self.session.begin():
            salon_stmt = select(DBsalon).where(DBsalon.id == appointment_data.salon_id)
            salon_result = await self.session.execute(salon_stmt)
            salon = salon_result.scalar_one_or_none()
            
            if not salon:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Salon not found"
                )
            
            master_stmt = select(DBmaster).where(DBmaster.id == appointment_data.master_id)
            master_result = await self.session.execute(master_stmt)
            master = master_result.scalar_one_or_none()
            
            if not master:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Master not found"
                )
            
            service_stmt = select(DBservice).where(DBservice.id == appointment_data.service_id)
            service_result = await self.session.execute(service_stmt)
            service = service_result.scalar_one_or_none()
            
            if not service:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Service not found"
                )
            
            end_time = appointment_data.date_time + timedelta(minutes=service.duration_minutes)
            
            overlap_stmt = select(DBappointment).where(
                and_(
                    DBappointment.master_id == appointment_data.master_id,
                    DBappointment.date_time < end_time,
                    DBappointment.end_time > appointment_data.date_time,
                    DBappointment.is_active == True
                )
            )
            overlap_result = await self.session.execute(overlap_stmt)
            if overlap_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This time slot overlaps with another appointment"
                )
            
            appointment = DBappointment(
                client_id=user_id,
                salon_id=appointment_data.salon_id,
                master_id=appointment_data.master_id,
                service_id=appointment_data.service_id,
                date_time=appointment_data.date_time,
                end_time=end_time,
                status=True,
                comment=appointment_data.comment or ""
            )
            
            self.session.add(appointment)
            await self.session.flush()
            await self.session.refresh(appointment)
            
            return {
                "message": "Appointment created successfully",
                "appointment": {
                    "id": appointment.id,
                    "salon_id": appointment.salon_id,
                    "master_id": appointment.master_id,
                    "service_id": appointment.service_id,
                    "date_time": appointment.date_time.isoformat(),
                    "end_time": appointment.end_time.isoformat(),
                    "status": appointment.status,
                    "comment": appointment.comment
                }
            }
    
    async def delete_appointment(
        self, 
        appointment_id: int, 
        user_id: int
    ) -> dict:
        """
        Удаление записи (soft delete)
        
        Args:
            appointment_id: ID записи
            user_id: ID пользователя
            
        Returns:
            dict: Сообщение об успехе
        """
        async with self.session.begin():
            stmt = select(DBappointment).where(DBappointment.id == appointment_id)
            result = await self.session.execute(stmt)
            appointment = result.scalar_one_or_none()
            
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Appointment not found"
                )
            
            if appointment.client_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have the right to delete this record"
                )
            
            if not appointment.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="This appointment has already been deleted"
                )
            
            appointment.is_active = False
            appointment.status = False
            
            return {
                "message": "Appointment deleted successfully",
                "appointment": {
                    "id": appointment.id,
                    "salon_id": appointment.salon_id,
                    "master_id": appointment.master_id,
                    "service_id": appointment.service_id,
                    "date_time": appointment.date_time.isoformat(),
                    "end_time": appointment.end_time.isoformat(),
                    "status": appointment.status,
                    "comment": appointment.comment
                }
            }

    async def get_free_slots(
        self,
        salon_id: int,
        service_id: int,
        target_date: date,
        master_id: int | None = None,
        min_hours_before: int = 2,
    ) -> list[dict]:
        """
        Получение свободных слотов для записи
        Рабочий день пока фиксированный: 10:00–19:00, обед 13:00–14:00
        
        Args:
            salon_id: ID салона
            service_id: ID услуги
            target_date: день в котором хотите записаться
            master_id: ID мастера к которому хотите записаться, Если master_id не задан или равен 0 — слоты для всех мастеров салона.
            min_hours_before: показать слоты после 2 часа     
            
        Returns:
            list[dict]: список свободных слотов
        
        """
        async with self.session.begin():
            salon_stmt = select(DBsalon).where(DBsalon.id == salon_id, DBsalon.is_active == True)
            salon_result = await self.session.execute(salon_stmt)
            salon = salon_result.scalar_one_or_none()
            if not salon:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Salon not found")

            service_stmt = select(DBservice).where(DBservice.id == service_id, DBservice.is_active == True)
            service_result = await self.session.execute(service_stmt)
            service = service_result.scalar_one_or_none()
            if not service:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

            service_duration = timedelta(minutes=service.duration_minutes)

            
            if master_id and master_id > 0:
                master_ids_stmt = select(DBmaster.id).where(DBmaster.id == master_id, DBmaster.is_active == True)
            else:
                master_ids_stmt = (
                    select(DBmaster.id)
                    .join(DBmaster_salon, DBmaster.id == DBmaster_salon.master_id)
                    .where(
                        and_(
                            DBmaster.is_active == True,
                            DBmaster_salon.salon_id == salon_id
                        )
                    )
                )
            master_ids_result = await self.session.execute(master_ids_stmt)
            master_ids = [row[0] for row in master_ids_result.fetchall()]
            if not master_ids:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Masters not found")

            work_start = datetime.combine(target_date, time(10, 0))
            work_end = datetime.combine(target_date, time(19, 0))
            lunch_start = datetime.combine(target_date, time(13, 0))
            lunch_end = datetime.combine(target_date, time(14, 0))
            now = datetime.now()
            min_start_time = now + timedelta(hours=min_hours_before)
            day_start = datetime.combine(target_date, time(0, 0))
            day_end = day_start + timedelta(days=1)

            def is_overlaps(start: datetime, end: datetime, intervals: list[tuple[datetime, datetime]]) -> bool:
                for s, e in intervals:
                    if start < e and end > s:
                        return True
                return False

            masters_slots: list[dict] = []

            for m_id in master_ids:
                appointments_stmt = select(DBappointment).where(
                    and_(
                        DBappointment.salon_id == salon_id,
                        DBappointment.master_id == m_id,
                        DBappointment.is_active == True,
                        DBappointment.date_time >= day_start,
                        DBappointment.date_time < day_end,
                    )
                )
                appointments_result = await self.session.execute(appointments_stmt)
                appointments: list[DBappointment] = appointments_result.scalars().all()

                busy_intervals: list[tuple[datetime, datetime]] = []
                for apt in appointments:
                    busy_intervals.append((apt.date_time, apt.end_time))

                free_slots: list[dict] = []
                current_start = work_start

                while current_start + service_duration <= work_end:
                    current_end = current_start + service_duration

                    if current_start < min_start_time:
                        current_start += timedelta(minutes=15)
                        continue

                    if current_start < lunch_end and current_end > lunch_start:
                        current_start = lunch_end
                        continue

                    if not is_overlaps(current_start, current_end, busy_intervals):
                        free_slots.append(
                            {
                                "start": current_start.isoformat(),
                                "end": current_end.isoformat(),
                            }
                        )

                    current_start += timedelta(minutes=15)

                masters_slots.append(
                    {
                        "master_id": m_id,
                        "slots": free_slots,
                    }
                )

            return masters_slots

