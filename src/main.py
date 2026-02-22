from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import auth, appointments, barbers, admin, reviews


app = FastAPI(
    title="Style and Barber API",
    description="Система онлайн-записи для салонов красоты",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(appointments.router)
app.include_router(barbers.router)
app.include_router(admin.router)
app.include_router(reviews.router)
app.include_router(reviews.admin_router)

@app.get("/")
async def root():
    return {"message": "Style and Barber API"}