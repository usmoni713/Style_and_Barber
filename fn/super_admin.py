from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from models.models import Admin, SalonEdit, SalonCreate, ServiceCreate, UserEdit, User
from sqlalchemy import delete, select, or_, and_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from database.setup import AssyncSessionLocal
from database.models import( users as DBUser,                            
                            appointments as DBappointment, 
                            salons as DBsalon,    
                            services as DBservice,
                            master_salon,
                            admins as DBadmin, 
                            admin_salon as DBadmin_salon
                            )

from security import security as sc
from security.additional_functions import hashing_password, verify_password

from fn import fns as fn

admin_router= APIRouter(prefix="/admin")


@admin_router.post("/admins")
async def add_admin_endpoint(admin_data: Admin, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
    """Создание нового админа (только для super_admin)"""
    async with AssyncSessionLocal() as session:
        async with session.begin():
            new_admin = DBadmin(
                phone = admin_data.phone,
                email = admin_data.email,
                password_hash = await hashing_password(admin_data.password),
                first_name = admin_data.name,
                last_name = admin_data.last_name,
                super_admin = admin_data.super_admin,    
            )
            session.add(new_admin)
            await session.flush()
            stmt = select(DBsalon).where(DBsalon.id.in_(admin_data.salons_id))
            result = await session.execute(stmt)
            salons = result.scalars().all()
            new_admin.salons = salons
            
            return {
                "message": "Admin created successfully",
                "admin": {
                    "id": new_admin.id,
                    "phone": admin_data.phone,
                    "email": admin_data.email,
                    "first_name": admin_data.name,
                    "last_name": admin_data.last_name,
                    "super_admin": admin_data.super_admin,
                    "salons": [salon.id for salon in salons]
                }
            }


@admin_router.delete("/admins/{admin_id}")
async def delete_admin_endpoint(admin_id: int, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
    async with AssyncSessionLocal() as session:
        async with session.begin():
            
            stmt_check = select(DBadmin).where(DBadmin.id == admin_id)
            result_check = await session.execute(stmt_check)
            admin_to_delete = result_check.scalar_one_or_none()
            
            if not admin_to_delete:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found"
                )
            
            if not admin_to_delete.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Admin has already been deleted"
                )
            
            stmt = (update(DBadmin).
                    where(and_(DBadmin.id==admin_id, DBadmin.is_active==True))
                    .values(is_active=False)
            )
            result = await session.execute(stmt)
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Admin not found or already deleted"
                )
            
            return {"message": f"Admin {admin_id} deleted successfully"}



@admin_router.post("/signin")
async def signin_admin_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):  
    async with AssyncSessionLocal() as session:
        login_value = form_data.username
        stmt = select(DBadmin).where(
            or_(DBadmin.email == login_value, DBadmin.phone == login_value)
        )
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()

        if admin:
            password_valid = await verify_password(
                password=form_data.password,
                hashed=admin.password_hash
            )
            if password_valid:
                if not admin.is_active:
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been banned")
                token = await sc.create_jwt_token({"admin_id": admin.id})
                return {"access_token": token, "token_type": "bearer"}

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )


@admin_router.get("/salons")
async def get_salons_admin_endpoint(admin:DBadmin = Depends(sc.get_admin_from_id)):
    salons_list = []
    async with AssyncSessionLocal() as session:
        stmt =(
                select(DBsalon)
                .join(DBadmin_salon, DBsalon.id == DBadmin_salon.salon_id)
                .where(DBadmin_salon.admin_id==admin.id)
                )
        result = await session.execute(stmt)
        admin_salons = result.scalars().all()
        
        for salon in admin_salons:
            salons_list.append({
                "id": salon.id,
                "title": salon.title,
                "address": salon.address,
                "phone": salon.phone,
                "photo_url": salon.photo_url
            })
        return salons_list
    

@admin_router.put("/salon/edit/info")
async def change_salon_admin_endpoint(salon_data: SalonEdit, admin: DBadmin = Depends(sc.get_admin_from_id)):
    async with AssyncSessionLocal() as session:
        async with session.begin():
            salon = await fn.get_salon_for_admin(admin_id=admin.id, salon_id=salon_data.id, session=session)
            salon.title = salon_data.title
            salon.address = salon_data.address
            salon.phone = salon_data.phone
            salon.photo_url = salon_data.photo_url    

            return {"message":"edited successfully"}
    

@admin_router.get("/salon/{salon_id}/masters")
async def get_masters_for_salon_admin_endpoint(salon_id: int, admin: DBadmin = Depends(sc.get_admin_from_id)):
    
    async with AssyncSessionLocal() as session:
        salon = await fn.get_salon_for_admin(admin_id=admin.id, salon_id=salon_id, session=session)
    
    masters = await fn.get_masters(salon_id=salon_id)
    return {"masters": masters}


@admin_router.delete("/salon/edit/delete_master")
async def delete_masters_for_salon_admin_endpoint(salon_id:int, master_id:int, admin:DBadmin = Depends(sc.get_admin_from_id)):
    async with AssyncSessionLocal() as session:
        async with session.begin():
            salon = await fn.get_salon_for_admin(admin_id=admin.id, salon_id=salon_id, session=session)
            stmt = delete(master_salon).where(and_(master_salon.salon_id==salon.id, master_salon.master_id==master_id))
            result = await session.execute(stmt)
            return {"data": f"master {master_id} deleted from salon {salon_id} "}
    

@admin_router.post("/salon/edit/add_master")
async def add_masters_for_salon_admin_endpoint(salon_id:int, master_email:str, admin:DBadmin = Depends(sc.get_admin_from_id)):
    async with AssyncSessionLocal() as session:
        async with session.begin():  
           
            
            salon = await fn.get_salon_for_admin(salon_id=salon_id, admin_id=admin.id, session=session, dowload_masters=True)
            stmt_user = select(DBUser).options(
                selectinload(DBUser.master)
            ).where(DBUser.email == master_email)
            result_user = await session.execute(stmt_user)
            dbuser = result_user.scalar_one_or_none()
            

            if not dbuser:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"User with email {master_email} not found"
                )
            
            
            dbmaster = dbuser.master[0]
            # TODO needs fixing! you need to check that the wizard associated with this user is 1, otherwise suggest choosing a specific wizard.
            if not dbmaster:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"User {master_email} is not a master"
                )
            
            
            if dbmaster in salon.masters:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail=f"Master {dbmaster.id} is already added to this salon"
                )
            
            
            salon.masters.append(dbmaster) 
            return {"data": f"master {dbmaster.id} successfully added"}


@admin_router.get("/salon/{salon_id}/appointments")
async def get_appointments_for_salon_admin_endpoint(salon_id: int, admin: DBadmin = Depends(sc.get_admin_from_id)):
    async with AssyncSessionLocal() as session:
        async with session.begin(): 
            salon = await fn.get_salon_for_admin(admin_id=admin.id, salon_id=salon_id, session=session, dowload_apponimens=True)
            appointments: list[DBappointment] = salon.appointments
            
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


@admin_router.delete("/salon/{salon_id}/appointments/{appointment_id}")
async def delete_appointment(salon_id: int, appointment_id: int, admin: DBadmin = Depends(sc.get_admin_from_id)):
    async with AssyncSessionLocal() as session:
        async with session.begin(): 
            salon = await fn.get_salon_for_admin(admin_id=admin.id, salon_id=salon_id, session=session)
            
           
            stmt_check = select(DBappointment).where(
                and_(
                    DBappointment.id == appointment_id,
                    DBappointment.salon_id == salon_id
                )
            )
            result_check = await session.execute(stmt_check)
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
            
            stmt = update(DBappointment).where(
                and_(
                    DBappointment.salon_id == salon_id,
                    DBappointment.id == appointment_id
                )
            ).values(is_active=False)
            result = await session.execute(stmt)
            return {"message": f"Appointment {appointment_id} deleted successfully"}



@admin_router.post("/salons", status_code=status.HTTP_201_CREATED)
async def create_salon_super_admin_endpoint(salon_data: SalonCreate, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
    """Создание нового салона (только для super_admin)"""
    async with AssyncSessionLocal() as session:
        async with session.begin():
            new_salon = DBsalon(
                title=salon_data.title,
                address=salon_data.address,
                phone=salon_data.phone,
                photo_url=salon_data.photo_url
            )
            session.add(new_salon)
            await session.flush()
            
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


@admin_router.put("/salons/{salon_id}")
async def update_salon_super_admin_endpoint(salon_id: int, salon_data: SalonCreate, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
   
    async with AssyncSessionLocal() as session:
        async with session.begin():
            stmt = select(DBsalon).where(DBsalon.id == salon_id)
            result = await session.execute(stmt)
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


@admin_router.post("/services", status_code=status.HTTP_201_CREATED)
async def create_service_super_admin_endpoint(service_data: ServiceCreate, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
    """Создание новой услуги (только для super_admin)"""
    async with AssyncSessionLocal() as session:
        async with session.begin():
            new_service = DBservice(
                description=service_data.description,
                duration_minutes=service_data.duration_minutes,
                base_price=service_data.base_price
            )
            session.add(new_service)
            await session.flush()
            
            return {
                "message": "Service created successfully",
                "service": {
                    "id": new_service.id,
                    "description": new_service.description,
                    "duration_minutes": new_service.duration_minutes,
                    "base_price": new_service.base_price
                }
            }


@admin_router.put("/services/{service_id}")
async def update_service_super_admin_endpoint(service_id: int, service_data: ServiceCreate, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
   
    async with AssyncSessionLocal() as session:
        async with session.begin():
            stmt = select(DBservice).where(DBservice.id == service_id)
            result = await session.execute(stmt)
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



@admin_router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user_super_admin_endpoint(user_data: User, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
    
    async with AssyncSessionLocal() as session:
        try:
            async with session.begin():
                new_user = DBUser(
                    first_name=user_data.name,
                    last_name=user_data.lastname,
                    email=user_data.email,
                    phone=user_data.phone,
                    password_hash=await hashing_password(user_data.password)
                )
                session.add(new_user)
                await session.flush()
                
                return {
                    "message": "User created successfully",
                    "user": {
                        "id": new_user.id,
                        "first_name": new_user.first_name,
                        "last_name": new_user.last_name,
                        "email": new_user.email,
                        "phone": new_user.phone
                    }
                }
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email or phone already exists"
            )


@admin_router.put("/users/{user_id}")
async def update_user_super_admin_endpoint(user_id: int, user_data: UserEdit, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
    
    async with AssyncSessionLocal() as session:
        async with session.begin():
            stmt = select(DBUser).where(DBUser.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Проверяем, что email/phone не заняты другими пользователями
            if user_data.email != user.email:
                stmt_check = select(DBUser).where(and_(DBUser.email == user_data.email, DBUser.id != user_id))
                result_check = await session.execute(stmt_check)
                if result_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User with this email already exists"
                    )
            
            if user_data.phone and user_data.phone != user.phone:
                stmt_check = select(DBUser).where(and_(DBUser.phone == user_data.phone, DBUser.id != user_id))
                result_check = await session.execute(stmt_check)
                if result_check.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User with this phone already exists"
                    )
            
            user.first_name = user_data.first_name
            user.last_name = user_data.last_name
            user.email = user_data.email
            user.phone = user_data.phone
            
            return {
                "message": "User updated successfully",
                "user": {
                    "id": user.id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "email": user.email,
                    "phone": user.phone
                }
            }


@admin_router.delete("/users/{user_id}")
async def delete_user_super_admin_endpoint(user_id: int, admin: DBadmin = Depends(sc.get_super_admin_from_id)):
    
    async with AssyncSessionLocal() as session:
        async with session.begin():
            stmt_check = select(DBUser).where(DBUser.id == user_id)
            result_check = await session.execute(stmt_check)
            user_to_delete = result_check.scalar_one_or_none()
            
            if not user_to_delete:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if not user_to_delete.is_active:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="User has already been deleted"
                )
            
            stmt = (update(DBUser).
                    where(and_(DBUser.id == user_id, DBUser.is_active == True))
                    .values(is_active=False)
            )
            result = await session.execute(stmt)
            
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or already deleted"
                )
            
            return {"message": f"User {user_id} deleted successfully"}

        
