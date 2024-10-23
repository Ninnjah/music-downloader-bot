from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

if TYPE_CHECKING:
    from .user import User


class DatesMixin:
    @declared_attr
    def created_on(self) -> Mapped[datetime]:
        return mapped_column(DateTime(), default=func.now(), server_default=func.now())

    @declared_attr
    def updated_on(self) -> Mapped[datetime]:
        return mapped_column(
            DateTime(),
            default=func.now(),
            server_default=func.now(),
            onupdate=func.now(),
            server_onupdate=func.now(),
        )


class UserRelationMixin:
    _user_back_populates: Optional[str] = None
    _user_unique: bool = False

    @declared_attr
    def user_id(self) -> Mapped[int]:
        return mapped_column(ForeignKey("users.id"), nullable=False, unique=self._user_unique)

    @declared_attr
    def user(self) -> Mapped["User"]:
        return relationship(
            "User",
            back_populates=self._user_back_populates,
            lazy="joined",
        )
