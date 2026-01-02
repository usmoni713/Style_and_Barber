from fastapi import APIRouter, Depends, Query

from src.services.salon_service import SalonService
from .depends_functions import get_salon_service

router = APIRouter(tags=["public"])


@router.get("/salons")
async def get_salons(
    service: SalonService = Depends(get_salon_service)
):
    """
    Получение списка всех салонов
    
    Returns:
        dict: Список салонов
    """
    salons = await service.get_all_salons()
    return {"salons": salons}


@router.get("/masters")
async def get_masters(
    salon_id: int | None = Query(None, description="ID салона для фильтрации"),
    service: SalonService = Depends(get_salon_service)
):
    """
    Получение списка мастеров
    
    Args:
        salon_id: Опциональный ID салона для фильтрации
        
    Returns:
        dict: Список мастеров
    """
    masters = await service.get_masters(salon_id=salon_id)
    return {"masters": masters}


@router.get("/services")
async def get_services(
    service: SalonService = Depends(get_salon_service)
):
    """
    Получение списка услуг
    
    Returns:
        dict: Список услуг
    """
    services = await service.get_services()
    return {"services": services}