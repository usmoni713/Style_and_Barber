from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin

class salons(Base, BaseMixin):
    __tablename__ = "salons"
    id: Mapped[int] = mapped_column(primary_key=True)
    title:Mapped[str]
    address:Mapped[str]
    phone : Mapped[str] = mapped_column(String(255))
    photo_url:Mapped[str]
    reason_for_deletion: Mapped[str | None]

    masters = relationship("masters", secondary="master_salon", back_populates="salons")
    appointments = relationship("appointments", back_populates="salon")
    admins = relationship("admins",secondary="admin_salon", back_populates="salons")
    services = relationship("services", secondary="service_salon", back_populates="salons")
    work_schedule = relationship("salon_schedules", back_populates="salon")

