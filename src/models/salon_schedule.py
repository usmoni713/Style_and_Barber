from datetime import time
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import  ForeignKey, PrimaryKeyConstraint, UniqueConstraint

from .Base import Base, BaseMixin



class salon_schedules(Base, BaseMixin):
    __tablename__ = "salon_schedules"
    __table_args__ = (
        PrimaryKeyConstraint( "salon_id", "day_of_week", name="pk_salon_day_of_week"),
        UniqueConstraint(    "salon_id", "day_of_week", name="uq_salon_day_of_week_pair"),
    ) 
    # id: Mapped[int] = mapped_column(primary_key=True)
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
    day_of_week: Mapped[int] # 0-6  0=понедельник
    start_time: Mapped[time] = mapped_column(nullable=True)
    end_time: Mapped[time] = mapped_column(nullable=True)
    break_start: Mapped[time] = mapped_column(nullable=True)
    break_end: Mapped[time] = mapped_column(nullable=True)
    is_working: Mapped[bool] = mapped_column(default=True)

    salon = relationship("salons", back_populates="work_schedule")
