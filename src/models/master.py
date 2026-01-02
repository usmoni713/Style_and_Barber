from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin


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

