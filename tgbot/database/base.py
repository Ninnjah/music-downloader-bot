from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    def to_dict(self):
        return {field.name: getattr(self, field.name) for field in self.__table__.c}

    def dict_to_insert(self):
        return {k: v for k, v in self.to_dict().items() if v}

    def __repr__(self):
        return (
            self.__class__.__name__
            + "("
            + ", ".join(f"{key}={value}" for key, value in self.to_dict().items())
            + ")"
        )
