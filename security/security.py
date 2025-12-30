import jwt
import datetime
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from config import ACCESS_TOKEN_EXPIRE_HOURS, ALGORITHM, SECRET_KEY


from sqlalchemy import select

from database.setup import AssyncSessionLocal
from database.models import users as DBUser, admins as DBadmin

oauth2_scheme_admin = OAuth2PasswordBearer(
    tokenUrl="/admin/signin",
    scheme_name="AdminAuth"
)
oauth2_scheme_user = OAuth2PasswordBearer(
    tokenUrl="/signin",
    scheme_name="UserAuth"
)

async def create_jwt_token(data:dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})  
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    

async def get_user_id_from_token(token = Depends(oauth2_scheme_user)):
    try:
        decode_token = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)

        return decode_token.get("user_id")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации") 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен устарел") 


async def get_user_from_id(user_id: str = Depends(get_user_id_from_token)):
    async with AssyncSessionLocal() as session:
        stmt  = select(DBUser).where(DBUser.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="Ошибка авторизации")
        return user


async def get_admin_id_from_token(token = Depends(oauth2_scheme_admin)):
    try:
        decode_token = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)

        return decode_token.get("admin_id")
    
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ошибка авторизации") 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен устарел") 


async def get_admin_from_id(admin_id: str = Depends(get_admin_id_from_token)):
    async with AssyncSessionLocal() as session:
        stmt  = select(DBadmin).where(DBadmin.id == admin_id)
        result = await session.execute(stmt)
        admin = result.scalar_one_or_none()
        if not admin:
            raise HTTPException(status_code=401, detail="Ошибка авторизации")
        if not admin.is_active:
            raise HTTPException(status_code=403, detail="your accaunt has been baned")
        return admin


async def get_super_admin_from_id(admin: DBadmin = Depends(get_admin_from_id)):
    if not admin.super_admin:
        raise HTTPException(status_code=403, detail="you are not super_admin")
    return admin


