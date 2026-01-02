from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base, BaseMixin


class admins(Base,BaseMixin):
    __tablename__ = "admins"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone : Mapped[str | None] = mapped_column(String(255), unique=True)
    email : Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str | None]
    super_admin: Mapped[bool | None]
    
    salons = relationship("salons",secondary="admin_salon", back_populates="admins")
    # def __repr__(self) -> str:
    #     return f"User(id={self.id!r}, phone={self.name!r}, fullname={self.fullname!r})"



