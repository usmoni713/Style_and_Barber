from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin

class service_category(Base, BaseMixin):
    __tablename__ = "service_category"
    id: Mapped[int] = mapped_column(primary_key=True)
    title:Mapped[str]
    services = relationship("services", back_populates="category") 


class services(Base, BaseMixin):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_category.id"), nullable=True) 
    description:Mapped[str]
    duration_minutes:Mapped[int]
    base_price:Mapped[int]

    masters = relationship("masters", secondary="master_service", back_populates="services")
    appointments = relationship("appointments", back_populates="service")
    category = relationship("service_category", back_populates="services", uselist=False)
    salons = relationship("salons", secondary="service_salon", back_populates="services")

