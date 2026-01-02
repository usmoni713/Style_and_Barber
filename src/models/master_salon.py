from sqlalchemy import  ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import  Mapped, mapped_column

from .Base import Base

    
class master_salon(Base):
    __tablename__ = "master_salon"
    __table_args__ = (
        PrimaryKeyConstraint("master_id", "salon_id", name="pk_master_salon"),
        UniqueConstraint("master_id", "salon_id", name="uq_master_salon_pair"),
    )
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
