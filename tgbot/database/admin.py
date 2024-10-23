from sqlalchemy import BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import DatesMixin


class Admin(Base, DatesMixin):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    sudo: Mapped[bool] = mapped_column(Boolean(), server_default="0")
