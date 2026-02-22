from enum import Enum as _enum
from datetime import datetime

from sqlalchemy import ForeignKey, String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin


class AppointmentStatus(_enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class appointments(Base, BaseMixin):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id:Mapped[int] = mapped_column(ForeignKey("users.id"))
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    date_time: Mapped[datetime]
    end_time:Mapped[datetime]
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.confirmed)
    comment:Mapped[str] = mapped_column(String(300))
    reason_for_deletion: Mapped[str | None]


    client = relationship("users", back_populates="appointments")
    salon = relationship("salons", back_populates="appointments")
    master = relationship("masters", back_populates="appointments")
    service = relationship("services", back_populates="appointments")
   