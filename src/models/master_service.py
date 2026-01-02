from sqlalchemy import  ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import  Mapped, mapped_column

from .Base import Base


class master_service(Base):
    __tablename__ = "master_service"
    __table_args__ = (
        PrimaryKeyConstraint("master_id", "service_id", name="pk_master_service"),
    )
    master_id: Mapped[int] = mapped_column(ForeignKey("masters.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    personal_price: Mapped[int | None]

