from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Query

from src.schemas import (
    AdminCreate, SalonEdit, SalonCreate, ServiceCreate,
    UserEdit, User, AdminEdit, MasterEdit
)
from src.models import admins as DBadmin

from src.core.security import get_super_admin_from_id, get_admin_from_id
from src.services.salon_service import SalonService
from src.services.admin_service import AdminService
from src.services.user_service import UserService
from src.services.service_service import ServiceService
from src.services.master_service import MasterService
from src.services.auth_service import AuthService

from .depends_functions import (
    get_admin_service, get_salon_service, get_user_service,
    get_service_service, get_master_service, get_auth_service
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/signin")
async def signin_admin(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """
    Авторизация администратора
    
    Args:
        form_data: Форма с username (email/phone) и password
        service: Сервис авторизации
        
    Returns:
        dict: JWT токен
    """
    return await service.authenticate_admin(form_data)


@router.get("/salons")
async def get_salons(
    admin: DBadmin = Depends(get_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Получение списка салонов администратора"""
    return await service.get_all_salons_for_admin(admin_id=admin.id)


@router.put("/salon/edit/info")
async def edit_salon(
    salon_data: SalonEdit,
    admin: DBadmin = Depends(get_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Редактирование информации о салоне"""
    return await service.edit_salon(salon_data=salon_data, admin_id=admin.id)


@router.get("/salon/{salon_id}/masters")
async def get_masters_for_salon(
    salon_id: int,
    admin: DBadmin = Depends(get_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Получение списка мастеров салона"""
    masters = await service.get_masters(salon_id=salon_id)
    return {"masters": masters}


@router.delete("/salon/edit/delete_master")
async def delete_master_from_salon(
    salon_id: int = Query(..., description="ID салона"),
    master_id: int = Query(..., description="ID мастера"),
    admin: DBadmin = Depends(get_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Удаление мастера из салона"""
    return await service.delete_master_from_salon(
        salon_id=salon_id,
        master_id=master_id,
        admin_id=admin.id
    )


@router.post("/salon/edit/add_master")
async def add_master_to_salon(
    salon_id: int = Query(..., description="ID салона"),
    master_email: str = Query(..., description="Email мастера"),
    admin: DBadmin = Depends(get_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Добавление мастера в салон"""
    return await service.add_master_to_salon(
        salon_id=salon_id,
        master_email=master_email,
        admin_id=admin.id
    )


@router.get("/salon/{salon_id}/appointments")
async def get_appointments_for_salon(
    salon_id: int,
    admin: DBadmin = Depends(get_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Получение всех записей салона"""
    return await service.get_appointments_for_salon(
        salon_id=salon_id,
        admin_id=admin.id
    )


@router.delete("/salon/{salon_id}/appointments/{appointment_id}")
async def delete_appointment_for_salon(
    salon_id: int,
    appointment_id: int,
    admin: DBadmin = Depends(get_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Удаление записи в салоне"""
    return await service.delete_appointment_for_salon(
        salon_id=salon_id,
        appointment_id=appointment_id,
        admin_id=admin.id
    )


@router.get("/salon/{salon_id}/users")
async def get_salon_users(
    salon_id: int,
    admin: DBadmin = Depends(get_admin_from_id),
    service: UserService = Depends(get_user_service)
):
    """Получение списка пользователей с записями в салоне"""
    users = await service.get_salon_users(salon_id=salon_id)
    return {"users": users}



@router.post("/admins", status_code=status.HTTP_201_CREATED)
async def create_admin(
    admin_data: AdminCreate,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: AdminService = Depends(get_admin_service)
):
    """Создание нового администратора (только для super_admin)"""
    return await service.create_admin(admin_data)


@router.put("/admins/{admin_id}")
async def update_admin(
    admin_id: int,
    admin_data: AdminEdit,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: AdminService = Depends(get_admin_service)
):
    """Редактирование администратора (только для super_admin)"""
    return await service.update_admin(admin_id, admin_data)


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: AdminService = Depends(get_admin_service)
):
    """Удаление администратора (только для super_admin)"""
    return await service.delete_admin(admin_id)


@router.get("/admins")
async def get_all_admins(
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: AdminService = Depends(get_admin_service)
):
    """Получение списка всех администраторов (только для super_admin)"""
    admins = await service.get_all_admins()
    return {"admins": admins}


@router.get("/salons/{salon_id}/admins")
async def get_salon_admins(
    salon_id: int,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: AdminService = Depends(get_admin_service)
):
    """Получение списка администраторов конкретного салона (только для super_admin)"""
    admins = await service.get_salon_admins(salon_id)
    return {"admins": admins}


@router.post("/salons", status_code=status.HTTP_201_CREATED)
async def create_salon(
    salon_data: SalonCreate,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Создание нового салона (только для super_admin)"""
    return await service.create_salon(salon_data)


@router.put("/salons/{salon_id}")
async def update_salon(
    salon_id: int,
    salon_data: SalonCreate,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Обновление салона (только для super_admin)"""
    return await service.update_salon(salon_id, salon_data)


@router.get("/salons/{salon_id}/masters")
async def get_salon_masters_super_admin(
    salon_id: int,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Получение списка мастеров конкретного салона (только для super_admin)"""
    masters = await service.get_masters(salon_id=salon_id)
    return {"masters": masters}


@router.post("/services", status_code=status.HTTP_201_CREATED)
async def create_service(
    service_data: ServiceCreate,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: ServiceService = Depends(get_service_service)
):
    """Создание новой услуги (только для super_admin)"""
    return await service.create_service(service_data)


@router.put("/services/{service_id}")
async def update_service(
    service_id: int,
    service_data: ServiceCreate,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: ServiceService = Depends(get_service_service)
):
    """Обновление услуги (только для super_admin)"""
    return await service.update_service(service_id, service_data)


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: User,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: UserService = Depends(get_user_service)
):
    """Создание нового пользователя (только для super_admin)"""
    return await service.create_user(user_data)


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserEdit,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: UserService = Depends(get_user_service)
):
    """Обновление пользователя (только для super_admin)"""
    return await service.update_user(user_id, user_data)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: UserService = Depends(get_user_service)
):
    """Удаление пользователя (только для super_admin)"""
    return await service.delete_user(user_id)


@router.get("/users")
async def get_all_users(
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: UserService = Depends(get_user_service)
):
    """Получение списка всех пользователей (только для super_admin)"""
    users = await service.get_all_users()
    return {"users": users}


@router.get("/masters")
async def get_all_masters(
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: SalonService = Depends(get_salon_service)
):
    """Получение списка всех мастеров (только для super_admin)"""
    masters = await service.get_masters()
    return {"masters": masters}


@router.put("/masters/{master_id}")
async def update_master(
    master_id: int,
    master_data: MasterEdit,
    admin: DBadmin = Depends(get_super_admin_from_id),
    service: MasterService = Depends(get_master_service)
):
    """Редактирование мастера (только для super_admin)"""
    return await service.update_master(master_id, master_data)

