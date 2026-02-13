from fastapi import APIRouter, Depends, Query
from datetime import date

from src.services.schedule_service import ScheduleService
from src.services.salon_service import SalonService
from src.services.appointment_service import AppointmentService
from src.schemas import ScheduleCreate
from .depends_functions import get_salon_service, get_appointment_service, get_schedule_service

router = APIRouter(prefix="/api/v1", tags=["public"])


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
    return {"status": "success", "data": {"salons": salons}}


@router.get("/masters")
async def get_masters(
    salon_id: int | None = Query(None, description="ID салона для фильтрации"),
    service_id: int | None = Query(None, description="ID услуги для фильтрации"),
    target_date: date | None = Query(None, description="Дата для фильтрации по доступности мастеров"),
    service: SalonService = Depends(get_salon_service)
):
    """
    Получение списка мастеров
    
    Args:
        salon_id: Опциональный ID салона для фильтрации
        service_id: Опциональный ID услуги для фильтрации
        
    Returns:
        dict: Список мастеров
    """
    masters = await service.get_masters(salon_id=salon_id, service_id=service_id, target_date=target_date)
    return {"status": "success", "data": {"masters": masters}}


@router.get("/services")
async def get_services(
    salon_id: int | None = Query(None, description="ID салона для фильтрации"),
    service: SalonService = Depends(get_salon_service)
):
    """
    Получение списка услуг
    
    Returns:
        dict: Список услуг
    """
    services = await service.get_services(salon_id=salon_id)
    return {"status": "success","data": {"services": services}}


@router.get("/free_slots")
async def get_free_slots(
    salon_id: int = Query(..., description="ID салона"),
    service_id: int = Query(..., description="ID услуги"),
    target_date: date = Query(..., description="Дата для поиска слотов (YYYY-MM-DD)"),
    master_id: int | None = Query(None, description="ID мастера (опционально, если не указан - слоты для всех мастеров)"),
    min_hours_before: int = Query(2, description="Минимальное количество часов до записи"),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """
    Получение свободных слотов для записи
    
    Args:
        salon_id: ID салона
        service_id: ID услуги
        target_date: Дата для поиска слотов
        master_id: Опциональный ID мастера
        min_hours_before: Минимальное количество часов до записи (по умолчанию 2)
        
    Returns:
        dict: Список свободных слотов по мастерам
    """
    slots = await appointment_service.get_free_slots(
        salon_id=salon_id,
        service_id=service_id,
        target_date=target_date,
        master_id=master_id,
        min_hours_before=min_hours_before
    )
    return {"status": "success", "data": {"slots": slots}}


@router.get("/salons/{salon_id}/schedule")
async def get_salon_schedule_by_id(
    salon_id: int,
    schedule_service: ScheduleService = Depends(get_schedule_service)):

    schedule = await schedule_service.get_salon_schedule(salon_id=salon_id)
    return {"status": "success", "data": {"salon_id": salon_id, "schedule": schedule}}

@router.get("/salons/{salon_id}/masters/{master_id}/schedule")
async def get_master_schedule_by_id(
    salon_id: int,
    master_id: int,
    schedule_service: ScheduleService = Depends(get_schedule_service)):

    schedule = await schedule_service.get_master_schedule(salon_id=salon_id, master_id=master_id)
    return {"status": "success", 
            "data": {
                "salon_id": salon_id,
                "master_id": master_id,
                "schedule": schedule}}


