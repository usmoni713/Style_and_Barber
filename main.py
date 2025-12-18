from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

from models.models import User, AppointmentCreate, AppointmentResponse

from sqlalchemy import select, exists, or_, and_

from database.setup import AssyncSessionLocal
from database.models import users as DBUser, masters as DBmaster, appointments as DBappointment, salons as DBsalon, services as DBservice, master_salon
from security import security as sc
# asyncpg.exceptions.UniqueViolationError
# sqlalchemy.exc.IntegrityError
from sqlalchemy.exc import IntegrityError


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from security.additional_functions import hashing_password, verify_password

@app.post("/singup")
async def add_user(user: User):
    try:
        async with AssyncSessionLocal() as session:
            async with session.begin():
                user = DBUser(
                    first_name=user.name,
                    last_name=user.lastname,
                    email=user.email,
                    phone=user.phone,
                    password_hash= await hashing_password(user.password) 
                ) 
                session.add(user)
           
        return {"data": "User created successfully"}
    except IntegrityError:
        raise HTTPException(status_code=409, detail="this email or phone number is already busy.")



@app.post("/singin")
async def singin(form_data: OAuth2PasswordRequestForm = Depends()):
  
    async with AssyncSessionLocal() as session:
        login_value = form_data.username
        stmt = select(DBUser).where(
            or_(DBUser.email == login_value, DBUser.phone == login_value)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            password_valid = await verify_password(
                password=form_data.password,
                hashed=user.password_hash
            )
            if password_valid:
                token = await sc.create_jwt_token({"user_id": user.id})
                return {"access_token": token, "token_type": "bearer"}

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
  

@app.get("/appointments", response_model=dict)
async def show_appointments(user: DBUser = Depends(sc.get_user_from_id)):
     
    async with AssyncSessionLocal() as session:

        stmt = select(DBappointment).where(and_(DBappointment.client_id == user.id, DBappointment.is_active == True))
        result = await session.execute(stmt)
        appointments = result.scalars().all()
        
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
                "created_at": apt.created_at.isoformat() if apt.created_at else None
            })
        
        return {"appointments": appointments_list}



@app.post("/appointments/add", response_model=dict)
async def add_appointment(
    appointment_data: AppointmentCreate,
    user: DBUser = Depends(sc.get_user_from_id)
):
   
    async with AssyncSessionLocal() as session:
        async with session.begin():
            
            salon_stmt = select(DBsalon).where(DBsalon.id == appointment_data.salon_id)
            salon_result = await session.execute(salon_stmt)
            salon = salon_result.scalar_one_or_none()
            
            if not salon:
                raise HTTPException(status_code=404, detail="Salon not found")
            
            master_stmt = select(DBmaster).where(DBmaster.id == appointment_data.master_id)
            master_result = await session.execute(master_stmt)
            master = master_result.scalar_one_or_none()
            
            if not master:
                raise HTTPException(status_code=404, detail="Master not found")
            
            service_stmt = select(DBservice).where(DBservice.id == appointment_data.service_id)
            service_result = await session.execute(service_stmt)
            service = service_result.scalar_one_or_none()
            
            if not service:
                raise HTTPException(status_code=404, detail="Service not found")
            
            
            existing_stmt = select(DBappointment).where(
                and_(
                    DBappointment.master_id == appointment_data.master_id,
                    DBappointment.date_time == appointment_data.date_time,
                    DBappointment.is_active == True  
                )
            )
            existing_result = await session.execute(existing_stmt)
            existing = existing_result.scalar_one_or_none()
            
            if existing:
                raise HTTPException(status_code=409, detail="This time slot is already booked")
            
            
            end_time = appointment_data.date_time + timedelta(minutes=service.duration_minutes)

            stmt = select(DBappointment).where(
                and_(
                    DBappointment.master_id == appointment_data.master_id,
                    # Пересечение интервалов:
                    DBappointment.date_time < end_time,
                    DBappointment.end_time > appointment_data.date_time,
                )
            )
            chec_if_not_free_time_result = await session.execute(stmt)
            chec_if_not_free_time = chec_if_not_free_time_result.scalar()
            if chec_if_not_free_time:
                raise HTTPException(status_code=409,detail="This time slot is already booked" )    
            appointment = DBappointment(
                client_id=user.id,
                salon_id=appointment_data.salon_id,
                master_id=appointment_data.master_id,
                service_id=appointment_data.service_id,
                date_time=appointment_data.date_time,
                end_time=end_time,
                status=True,  
                comment=appointment_data.comment or ""
            )
            session.add(appointment)
            await session.flush()  
            await session.refresh(appointment)
        
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


@app.get("/salons")
async def get_salons():
    """Получить список всех салонов"""
    async with AssyncSessionLocal() as session:
        stmt = select(DBsalon).where(DBsalon.is_active == True)
        result = await session.execute(stmt)
        salons = result.scalars().all()
        
        salons_list = []
        for salon in salons:
            salons_list.append({
                "id": salon.id,
                "title": salon.title,
                "address": salon.address,
                "phone": salon.phone,
                "photo_url": salon.photo_url
            })
        
        return {"salons": salons_list}


@app.get("/masters")
async def get_masters(salon_id: int = None):
    """Получить список мастеров (опционально фильтр по салону)"""
    async with AssyncSessionLocal() as session:
        if salon_id: 
            stmt = (
                select(DBmaster)
                .join(master_salon, DBmaster.id == master_salon.master_id)
                .where(
                    and_(
                        DBmaster.is_active == True,
                        master_salon.salon_id == salon_id
                    )
                )
            )
        else:
            stmt = select(DBmaster).where(DBmaster.is_active == True)
        
        result = await session.execute(stmt)
        masters = result.scalars().all()
        
        masters_list = []
        for master in masters:
            masters_list.append({
                "id": master.id,
                "photo": master.photo,
                "specialization": master.specialization,
                "about": master.about,
                "user_id": master.user_id
            })
        
        return {"masters": masters_list}


@app.get("/services")
async def get_services():
    """Получить список всех услуг"""
    async with AssyncSessionLocal() as session:
        stmt = select(DBservice).where(DBservice.is_active == True)
        result = await session.execute(stmt)
        services = result.scalars().all()
        
        services_list = []
        for service in services:
            services_list.append({
                "id": service.id,
                "description": service.description,
                "duration_minutes": service.duration_minutes,
                "base_price": service.base_price
            })
        
        return {"services": services_list}


@app.delete("/del_appointment")
async def delete_appointment(
    appointment_id: int,
    user: DBUser = Depends(sc.get_user_from_id)
):
    async with AssyncSessionLocal() as session:
        async with session.begin():
            stmt = select(DBappointment).where(DBappointment.id == appointment_id)
            appointment_result = await session.execute(stmt)
            appointment = appointment_result.scalar_one_or_none()
            if not appointment:
                raise HTTPException(status_code=415, detail="Record not found")
            
            if appointment.client_id != user.id:
                raise HTTPException(status_code=403, detail="You do not have the right to delete this record")
            if not appointment.is_active:
                    raise HTTPException(status_code=410, detail="This entry has already been deleted")
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
            







