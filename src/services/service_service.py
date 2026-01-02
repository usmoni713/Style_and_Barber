from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.models import services as DBservice
from src.repository.base_repo import BaseRepository
from src.schemas import ServiceCreate


class ServiceService:
    """Сервис для работы с услугами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(DBservice, session)
    
    async def create_service(self, service_data: ServiceCreate) -> dict:
        """Создание новой услуги"""
        async with self.session.begin():
            new_service = DBservice(
                description=service_data.description,
                duration_minutes=service_data.duration_minutes,
                base_price=service_data.base_price
            )
            self.session.add(new_service)
            await self.session.flush()
            
            return {
                "message": "Service created successfully",
                "service": {
                    "id": new_service.id,
                    "description": new_service.description,
                    "duration_minutes": new_service.duration_minutes,
                    "base_price": new_service.base_price
                }
            }
    
    async def update_service(self, service_id: int, service_data: ServiceCreate) -> dict:
        """Обновление услуги"""
        async with self.session.begin():
            stmt = select(DBservice).where(DBservice.id == service_id)
            result = await self.session.execute(stmt)
            service = result.scalar_one_or_none()
            
            if not service:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Service not found"
                )
            
            service.description = service_data.description
            service.duration_minutes = service_data.duration_minutes
            service.base_price = service_data.base_price
            
            return {
                "message": "Service updated successfully",
                "service": {
                    "id": service.id,
                    "description": service.description,
                    "duration_minutes": service.duration_minutes,
                    "base_price": service.base_price
                }
            }

