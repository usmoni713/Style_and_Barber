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

    masters = relationship("masters", secondary="master_salon", back_populates="salons")
    appointments = relationship("appointments", back_populates="salon")
    admins = relationship("admins",secondary="admin_salon", back_populates="salons")
    services = relationship("services", secondary="service_salon", back_populates="salons")
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
    