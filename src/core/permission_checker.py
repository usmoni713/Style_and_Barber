from fastapi import HTTPException, status
from functools import wraps
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.schemas import SalonEdit
from src.models import (salons as DBsalon,
                        masters as DBmaster,
                        master_salon as DBmaster_salon,
                        services as DBservice,
                        admin_salon as DBadmin_salon,
                        admins as DBadmin,
                        service_salon as DBservice_salon

) 
from src.repository.base_repo import BaseRepository

from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from src.services.schedule_service import ScheduleService


class СheckingAdminAccessSalon:
    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            admin = kwargs.get("admin")  
            if admin.super_admin:  # СуперАдмин всегда имеет доступ ко всему
                return await func(*args, **kwargs)
            
            salon_id = kwargs.get("salon_id")  
            if salon_id not in [salon_.id for salon_ in admin.salons]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для доступа к этому салону"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    



