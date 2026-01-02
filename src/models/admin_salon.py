from sqlalchemy import  ForeignKey, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.orm import  Mapped, mapped_column

from .Base import Base

class admin_salon(Base):
    __tablename__ = "admin_salon"
    __table_args__ = (
        PrimaryKeyConstraint("admin_id", "salon_id", name="pk_admin_salon"),
        UniqueConstraint("admin_id", "salon_id", name="uq_admin_salon_pair"),
    )
    admin_id: Mapped[int] = mapped_column(ForeignKey("admins.id"))
    salon_id: Mapped[int] = mapped_column(ForeignKey("salons.id"))
