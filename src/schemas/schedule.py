from pydantic import BaseModel, EmailStr
from datetime import time


class DaySchedule(BaseModel):
    """Схема для расписаний"""
    day_of_week: int
    start_time: time # формат "HH:MM"
    end_time: time
    break_start: time | None
    break_end: time | None
    is_working: bool


class ScheduleCreate(BaseModel):
    Schedules: list[DaySchedule]

# class ScheduleResponse(BaseModel):
#     pass TODO: Добавить схему ответа

