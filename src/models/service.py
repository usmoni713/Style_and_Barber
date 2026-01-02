from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin


class services(Base, BaseMixin):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    # category_id: Mapped[int] = mapped_column(primary_key=True) 
    description:Mapped[str]
    duration_minutes:Mapped[int]
    base_price:Mapped[int]

    masters = relationship("masters", secondary="master_service", back_populates="services")
    appointments = relationship("appointments", back_populates="service")
    