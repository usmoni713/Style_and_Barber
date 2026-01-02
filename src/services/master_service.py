from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from src.models import masters as DBmaster
from src.repository.base_repo import BaseRepository
from src.schemas import MasterEdit


class MasterService:
    """Сервис для работы с мастерами"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = BaseRepository(DBmaster, session)
    
    async def update_master(self, master_id: int, master_data: MasterEdit) -> dict:
        """Обновление мастера"""
        async with self.session.begin():
            stmt = select(DBmaster).where(DBmaster.id == master_id)
            result = await self.session.execute(stmt)
            master = result.scalar_one_or_none()
            
            if not master:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Master not found"
                )
            
            master.photo = master_data.photo
            master.specialization = master_data.specialization
            master.about = master_data.about
            
            return {
                "message": "Master updated successfully",
                "master": {
                    "id": master.id,
                    "user_id": master.user_id,
                    "photo": master.photo,
                    "specialization": master.specialization,
                    "about": master.about
                }
            }

