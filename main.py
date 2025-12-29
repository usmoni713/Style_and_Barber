from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select, or_

from database.setup import AssyncSessionLocal
from database.models import (users as DBUser, 
                            admins as DBadmin)

from security import security as sc

from fn import fns as fn
from fn.users import user_router
from fn.super_admin import admin_router

from security.additional_functions import verify_password

app = FastAPI()
app.include_router(user_router)
app.include_router(admin_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/signin")
async def signin_user_endpoint(form_data: OAuth2PasswordRequestForm = Depends()):
    """Эндпоинт для авторизации пользователей (не админов)"""
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
    

@app.get("/salons")
async def get_salons_endpoint():
    salons_list = await fn.get_all_salons()
    return {"salons": salons_list}


@app.get("/masters")
async def get_masters_endpoint(salon_id: int = None):
    masters_list = await fn.get_masters(salon_id=salon_id)
    return {"masters": masters_list}


@app.get("/services")
async def get_services_endpoint():
    services_list = await fn.get_services()
    return {"services": services_list}

