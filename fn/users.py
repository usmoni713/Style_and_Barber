from fastapi import Depends, HTTPException, status, APIRouter

from models.models import User, AppointmentCreate

from database.models import users as DBUser
from security import security as sc
from fn import fns as fn



user_router = APIRouter(prefix="/user")



@user_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def add_user_endpoint(user: User):
    await fn.create_user(user)
    return {"message": "User created successfully"}
  
@user_router.get("/appointments", response_model=dict)
async def show_appointments_endpoint(user: DBUser = Depends(sc.get_user_from_id)):
    appointments_list = await fn.get_apponimints(user) 
    return {"appointments": appointments_list}



@user_router.post("/appointments/add", response_model=dict)
async def add_appointment_endpoint(
    appointment_data: AppointmentCreate,
    user: DBUser = Depends(sc.get_user_from_id)
):
   answer = await fn.add_apponiment(appointment_data, user.id)
   return answer


@user_router.delete("/appointments/{appointment_id}")
async def delete_appointment_endpoint(
    appointment_id: int,
    user: DBUser = Depends(sc.get_user_from_id)
):
    answer = await fn.delete_appointment(appointment_id, user)
    return answer
            















