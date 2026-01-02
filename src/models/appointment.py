from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin


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
   