from typing import Optional

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .mixins import DatesMixin


class User(Base, DatesMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger(), primary_key=True)
    firstname: Mapped[str] = mapped_column(String(), nullable=False)
    lastname: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(), nullable=True)
    banned: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False, server_default="0")
