from sqlalchemy import  ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import  Mapped, mapped_column

from .Base import Base

    
class service_salon(Base):
    __tablename__ = "service_salon"
    __table_args__ = (
        PrimaryKeyConstraint("service_id", "salon_id", name="pk_service_salon"),
        UniqueConstraint("service_id", "salon_id", name="uq_service_salon_pair"),
    )
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
