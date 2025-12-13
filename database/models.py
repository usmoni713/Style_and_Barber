from typing import List
from datetime import datetime, timezone


from sqlalchemy import CheckConstraint, ForeignKey, PrimaryKeyConstraint, UniqueConstraint, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.orm.writeonly import interfaces
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, DateTime, Boolean, func
# from sqlalchemy.orm import relationship



class BaseMixin:
    """Миксин с общими полями для всех таблиц."""
    
    @declared_attr
    def created_at(cls):
        # Устанавливает время в UTC при создании записи
        return Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    @declared_attr
    def is_active(cls):
        return Column(Boolean, default=True, nullable=False)
    

class Base(DeclarativeBase):
    pass

class users(Base,BaseMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone : Mapped[str | None] = mapped_column(String(255), unique=True)
    email : Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str | None]

    master = relationship("masters", back_populates="user")
    appointments = relationship("appointments", back_populates="client")

    
    
    # def __repr__(self) -> str:
    #     return f"User(id={self.id!r}, phone={self.name!r}, fullname={self.fullname!r})"


class salons(Base, BaseMixin):
    __tablename__ = "salons"
    id: Mapped[int] = mapped_column(primary_key=True)
    title:Mapped[str]
    address:Mapped[str]
    phone : Mapped[str] = mapped_column(String(255))
    # work_schedule:Mapped[dict] 
#     {
#   "monday": { "start": "09:00", "end": "18:00", "break_start": "13:00", "break_end": "14:00" },
#   "tuesday": { "start": "09:00", "end": "18:00", "break_start": "13:00", "break_end": "14:00" },
#   "wednesday": { "start": "09:00", "end": "18:00", "break_start": "13:00", "break_end": "14:00" },
#   "thursday": { "start": "09:00", "end": "18:00", "break_start": "13:00", "break_end": "14:00" },
#   "friday": { "start": "09:00", "end": "18:00", "break_start": "13:00", "break_end": "14:00" },
#   "saturday": null,
#   "sunday": null
# }
    photo_url:Mapped[str]
    
    # салон может иметь много мастеров

    masters = relationship("masters", secondary="master_salon", back_populates="salons")
    appointments = relationship("appointments", back_populates="salon")
    

class masters(Base, BaseMixin):
    __tablename__ = "masters"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    photo:Mapped[str]
    specialization:Mapped[str]
    about:Mapped[str]
    
    user = relationship("users", back_populates="master", uselist=False)
    # мастер может работать в нескольких салонах
    salons = relationship("salons", secondary="master_salon", back_populates="masters")

    services = relationship("services", secondary="master_service", back_populates="masters")
    appointments = relationship("appointments", back_populates="master")


class services(Base, BaseMixin):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    # category_id: Mapped[int] = mapped_column(primary_key=True) 
    description:Mapped[str]
    duration_minutes:Mapped[int]
    base_price:Mapped[int]

    masters = relationship("masters", secondary="master_service", back_populates="services")
    appointments = relationship("appointments", back_populates="service")
    
class master_salon(Base):
    __tablename__ = "master_salon"
    __table_args__ = (
        PrimaryKeyConstraint("master_id", "salon_id", name="pk_master_salon"),
        UniqueConstraint("master_id", "salon_id", name="uq_master_salon_pair"),
    )
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))


class master_service(Base):
    __tablename__ = "master_service"
    __table_args__ = (
        PrimaryKeyConstraint("master_id", "service_id", name="pk_master_service"),
    )
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    personal_price: Mapped[int | None]


 
class appointments(Base, BaseMixin):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id:Mapped[int] = mapped_column(ForeignKey("users.id"))
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    date_time: Mapped[datetime]
    end_time:Mapped[datetime]
    status: Mapped[bool]
    comment:Mapped[str] = mapped_column(String(300))


    client = relationship("users", back_populates="appointments")
    salon = relationship("salons", back_populates="appointments")
    master = relationship("masters", back_populates="appointments")
    service = relationship("services", back_populates="appointments")
    

  
# class working_hours(Base):
#     __tablename__ = "working_hours"
#     id: Mapped[int] = mapped_column(primary_key=True)

#     master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
#     salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
#     day_of_week: Mapped(int)
#     start_time:


#     __table_args__ = (
#         CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='check_day_of_week_range'),
#         # или просто:
#         # CheckConstraint('day_of_week BETWEEN 0 AND 6', name='check_day_of_week_range_alt')
#     )







