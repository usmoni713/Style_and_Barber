from sqlalchemy import ForeignKey, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin


class reviews(Base, BaseMixin):
    """Модель отзыва о мастере или салоне"""
    
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    master_id: Mapped[int | None] = mapped_column(ForeignKey("masters.id"), nullable=True)
    salon_id: Mapped[int | None] = mapped_column(ForeignKey("salons.id"), nullable=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), nullable=False, unique=True)
    
    rating: Mapped[int]  # 1-5 звёзд
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_moderated: Mapped[bool] = mapped_column(Boolean, default=False)
    reason_for_deletion: Mapped[str | None]
    
    user = relationship("users", back_populates="reviews")
    master = relationship("masters", back_populates="reviews")
    salon = relationship("salons", back_populates="reviews")
    appointment = relationship("appointments", back_populates="review")
    
