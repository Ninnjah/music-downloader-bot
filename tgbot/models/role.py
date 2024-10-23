from enum import Enum


class UserRole(Enum):
    SUDO = "sudo"
    ADMIN = "admin"
    USER = "user"
