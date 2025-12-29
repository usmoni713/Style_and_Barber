from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from models.models import Admin, SalonEdit
from sqlalchemy import delete, select, or_, and_, update
from sqlalchemy.orm import selectinload
from database.setup import AssyncSessionLocal
from database.models import( users as DBUser,                            
                            appointments as DBappointment, 
                            salons as DBsalon,    
                            master_salon,
                            admins as DBadmin, 
                            admin_salon as DBadmin_salon
                            )

from security import security as sc
from security.additional_functions import verify_password

from fn import fns as fn

admin_router= APIRouter(prefix="/admin")


@admin_router.post("/add_admin")
async def add_admin_endpoint(admin_data: Admin):
    # await fn.create_user(user)
    # TODO: добавить админа в бд
    pass


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
    

@admin_router.post("/salon/edit/info")
async def change_salon_admin_endpoint(salon_data:SalonEdit,  admin:DBadmin = Depends(sc.get_admin_from_id) ):
    async with AssyncSessionLocal() as session:
        async with session.begin():
            salon = await fn.get_salon_for_admin(admin_id=admin.id, salon_id=salon_data.id, session=session)
            salon.title = salon_data.title
            salon.address = salon_data.address
            salon.phone = salon_data.phone
            salon.photo_url = salon_data.photo_url    

            return {"message":"edited successfully"}
    

@admin_router.get("/salon/get_masters")
async def get_masters_for_salon_admin_endpoint(salon_id:int, admin:DBadmin = Depends(sc.get_admin_from_id)):
    if not salon_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="the salon ID has not been entered")
    masters = await fn.get_masters(salon_id=salon_id)
    return masters


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


@admin_router.get("/salon/apponiments")
async def get_apponiments_for_salon_admin_endpoint(salon_id:int, admin:DBadmin = Depends(sc.get_admin_from_id)):
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


@admin_router.post("/salon/edit/delete_apponiment")
async def delete_apponiment(salon_id:int, apponiment_id:int,admin:DBadmin = Depends(sc.get_admin_from_id) ):
    async with AssyncSessionLocal() as session:
        async with session.begin(): 
            salon = await fn.get_salon_for_admin(admin_id=admin.id, salon_id=salon_id, session=session)
            stmt = update(DBappointment).where(and_(DBappointment.salon_id==salon_id,
                                                    DBappointment.id == apponiment_id
                                                    )).values(is_active=False)
            result = await session.execute(stmt)
            return {"data":f"apponiment {apponiment_id} deleted"}
        

        
