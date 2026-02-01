from pprint import pprint
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, date, time, timedelta
from fastapi import HTTPException, status

from src.models import (
    appointments as DBappointment,
    salons as DBsalon,
    masters as DBmaster,
    services as DBservice,
    master_salon as DBmaster_salon,
    salon_schedules as DBsalon_schedules,
    master_schedules as DBmaster_schedules
)
from src.schemas import ScheduleCreate, DaySchedule

class ScheduleService:

    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_salon_schedule(self, salon_id: int):
        stmt = select(DBsalon_schedules).where(DBsalon_schedules.salon_id==salon_id, DBsalon_schedules.is_working==True)
        result = await self.session.execute(stmt)
        salon_schedules = result.scalars().all()
        salon_schedules_list = []
        for salon_schedule in salon_schedules:
            salon_schedules_list.append(DaySchedule(
                day_of_week=salon_schedule.day_of_week,
                start_time=salon_schedule.start_time,
                end_time=salon_schedule.end_time,
                break_start=salon_schedule.break_start,
                break_end=salon_schedule.break_end,
                is_working=salon_schedule.is_working
                )
            )
        return salon_schedules_list

    async def update_salon_schedule(self, salon_id, schedule_data: ScheduleCreate):
        async with self.session.begin():
            delete_stmt = select(DBsalon_schedules).where(DBsalon_schedules.salon_id == salon_id)
            result = await self.session.execute(delete_stmt)
            existing_schedules = result.scalars().all()
            for schedule in existing_schedules:
                await self.session.delete(schedule)


            for day_schedule in schedule_data.Schedules:
                new_schedule = DBsalon_schedules(
                    salon_id=salon_id,
                    day_of_week=day_schedule.day_of_week,
                    start_time=day_schedule.start_time,
                    end_time=day_schedule.end_time,
                    break_start=day_schedule.break_start,
                    break_end=day_schedule.break_end,
                    is_working=day_schedule.is_working
                )
                self.session.add(new_schedule)
        
        return {"message": "Расписание успешно обновлено"}

    async def get_master_schedule(self, master_id: int, salon_id: int):
        stmt = select(DBmaster_schedules).where(and_(
            DBmaster_schedules.master_id==master_id,
            DBmaster_schedules.salon_id==salon_id,
            DBmaster_schedules.is_working==True
        ))
        result = await self.session.execute(stmt)
        master_schedules = result.scalars().all()
        master_schedules_list = []
        for master_schedule in master_schedules:
            master_schedules_list.append(DaySchedule(
                day_of_week=master_schedule.day_of_week,
                start_time=master_schedule.start_time,
                end_time=master_schedule.end_time,
                break_start=master_schedule.break_start,
                break_end=master_schedule.break_end,
                is_working=master_schedule.is_working
                )
            )
        return master_schedules_list

    async def update_master_schedule(self, master_id: int, salon_id: int, schedule_data: ScheduleCreate):
        async with self.session.begin():
            delete_stmt = select(DBmaster_schedules).where(
                and_(
                    DBmaster_schedules.master_id == master_id,
                    DBmaster_schedules.salon_id == salon_id
                )
            )
            result = await self.session.execute(delete_stmt)
            existing_schedules = result.scalars().all()
            for schedule in existing_schedules:
                await self.session.delete(schedule)

            for day_schedule in schedule_data.Schedules:
                new_schedule = DBmaster_schedules(
                    master_id=master_id,
                    salon_id=salon_id,
                    day_of_week=day_schedule.day_of_week,
                    start_time=day_schedule.start_time,
                    end_time=day_schedule.end_time,
                    break_start=day_schedule.break_start,
                    break_end=day_schedule.break_end,
                    is_working=day_schedule.is_working
                )
                self.session.add(new_schedule)
        
        return {"message": "Расписание мастера успешно обновлено"}

    async def get_available_masters(self, salon_id: int, service_id: int, target_date: date):

        stmt = select(DBmaster_schedules).where(
            and_(
                DBmaster_schedules.salon_id == salon_id,
                DBmaster_schedules.is_working == True
            )
        )
        result = await self.session.execute(stmt)
        master_schedules = result.scalars().all()
        available_masters = []
        for master_schedule in master_schedules:
            if master_schedule.day_of_week != target_date.weekday():
                continue

            service_stmt = select(DBservice).where(DBservice.id == service_id)
            service_result = await self.session.execute(service_stmt)
            service = service_result.scalars().first()
            if not service:
                continue

            target_datetime_start = datetime.combine(target_date, master_schedule.start_time)
            target_datetime_end = datetime.combine(target_date, master_schedule.end_time)

            current_time = target_datetime_start
            while current_time + timedelta(minutes=service.duration_minutes) <= target_datetime_end:
                is_available = await self.is_time_available(
                    salon_id,
                    master_schedule.master_id,
                    current_time,
                    service.duration_minutes
                )
                if is_available:
                    available_masters.append(master_schedule.master_id)
                    break
                current_time += timedelta(minutes=15)

        return available_masters
    
    async def is_time_available(self, salon_id: int, master_id: int, target_datetime: datetime, duration_minutes: int):
        
        day_of_week = target_datetime.weekday()  # 0=Monday 6=Sunday
        time_of_day = target_datetime.time()
        end_time = (datetime.combine(date.min, time_of_day) + timedelta(minutes=duration_minutes)).time()

        salon_stmt = select(DBsalon_schedules).where(
            and_(
                DBsalon_schedules.salon_id == salon_id,
                DBsalon_schedules.day_of_week == day_of_week,
                DBsalon_schedules.is_working == True
            )
        )
        master_stmt = select(DBmaster_schedules).where(
            and_(
                DBmaster_schedules.salon_id == salon_id,
                DBmaster_schedules.master_id == master_id,
                DBmaster_schedules.day_of_week == day_of_week,
                DBmaster_schedules.is_working == True
            )
        )

        salon_result = await self.session.execute(salon_stmt)
        master_result = await self.session.execute(master_stmt)

        salon_schedule = salon_result.scalars().first()
        master_schedule = master_result.scalars().first()

        if not salon_schedule or not master_schedule:
            return False

        def is_within_schedule(schedule):
            if schedule.break_start and schedule.break_end:
                return (schedule.start_time <= time_of_day < schedule.break_start) or (schedule.break_end < end_time <= schedule.end_time)
            else:
                return schedule.start_time <= time_of_day and end_time <= schedule.end_time

        if not is_within_schedule(salon_schedule) or not is_within_schedule(master_schedule):
            return False

        appointment_stmt = select(DBappointment).where(
            and_(
                DBappointment.salon_id == salon_id,
                DBappointment.master_id == master_id,
                DBappointment.date_time < target_datetime + timedelta(minutes=duration_minutes),
                DBappointment.end_time > target_datetime
            ) 
        )
        appointment_result = await self.session.execute(appointment_stmt)
        overlapping_appointments = appointment_result.scalars().all()

        return len(overlapping_appointments) == 0



