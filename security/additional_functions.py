import bcrypt, asyncio


async def hashing_password(password: str) -> str:

    salt = bcrypt.gensalt()

    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


async def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))



async def test():
    t = '1234'
    h  = await hashing_password(t)
    res = await verify_password("2345", h)
    print(res)

if __name__ == "__main__":
    asyncio.run(test())
