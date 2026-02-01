from datetime import time
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import  ForeignKey, PrimaryKeyConstraint, UniqueConstraint

from .Base import Base, BaseMixin



class master_schedules(Base, BaseMixin):
    __tablename__ = "master_schedules"
    __table_args__ = (
        PrimaryKeyConstraint("master_id", "salon_id", "day_of_week", name="pk_master_salon_day_of_week"),
        UniqueConstraint("master_id", "salon_id", "day_of_week", name="uq_master_salon_day_of_week_pair"),
    )
    # id: Mapped[int] = mapped_column(primary_key=True)
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))

    day_of_week: Mapped[int] # 0-6  0=понедельник
    start_time: Mapped[time] = mapped_column(nullable=True)
    end_time: Mapped[time] = mapped_column(nullable=True)
    break_start: Mapped[time] = mapped_column(nullable=True)
    break_end: Mapped[time] = mapped_column(nullable=True)
    is_working: Mapped[bool] = mapped_column(default=True)

    # salon = relationship("salons", back_populates="work_schedule")
    master = relationship("masters", back_populates="work_schedule")
