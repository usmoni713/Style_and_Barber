import jwt
import datetime
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException
from config import ACCESS_TOKEN_EXPIRE_HOURS, ALGORITHM, SECRET_KEY


from sqlalchemy import select, exists, or_, and_

from database.setup import AssyncSessionLocal
from database.models import users as DBUser, masters as DBmaster

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/singin")

async def create_jwt_token(data:dict):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})  
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    

async def get_user_id_from_token(token = Depends(oauth2_scheme)):
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
