from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin


class users(Base,BaseMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone : Mapped[str | None] = mapped_column(String(255), unique=True)
    email : Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str | None]

    master = relationship("masters", back_populates="user")
    appointments = relationship("appointments", back_populates="client")
