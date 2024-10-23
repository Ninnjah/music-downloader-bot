import logging
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.row import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.database import Admin, User

logger = logging.getLogger(__name__)


# TODO ADD LAYERS
class Repo:
    """Db abstraction layer"""

    def __init__(self, session: AsyncSession):
        self._session = session

    # users
    async def add_user(self, user: User) -> None:
        """Store user in DB, on conflict updates user information"""
        stmt = insert(User).values(user.dict_to_insert())
        stmt = stmt.on_conflict_do_update(
            constraint=User.__table__.primary_key,
            set_=dict(
                firstname=stmt.excluded.firstname,
                lastname=stmt.excluded.lastname,
                username=stmt.excluded.username,
            ),
        )

        await self._session.execute(stmt)
        await self._session.commit()

    async def get_user(self, user_id: int) -> Optional[User]:
        """Returns user from DB by user id"""
        stmt = select(User).where(User.id == user_id)

        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_users(self) -> Sequence[User]:
        """List all bot users"""
        stmt = select(User).order_by(User.created_on)

        res = await self._session.execute(stmt)
        return res.scalars().all()

    async def stats_users(self) -> RowMapping:
        """List income stats about users"""
        last_day = datetime.now() - timedelta(days=1)
        last_week = datetime.now() - timedelta(days=7)
        stmt = select(
            func.count(case((User.__table__.c.created_on >= last_day, 1))).label("today"),
            func.count(case((User.__table__.c.created_on >= last_week, 1))).label("week"),
            func.count(User.id).label("total"),
        )

        res = await self._session.execute(stmt)
        return res.mappings().one()

    async def set_user_ban(self, user_id: int, banned: bool) -> None:
        """Set user ban status

        :param user_id: User telegram id
        :type user_id: int
        :param banned: New user ban status
        :type banned: bool
        """
        stmt = update(User).where(User.id == user_id).values(banned=banned)

        await self._session.execute(stmt)
        await self._session.commit()

    # admins
    async def add_admin(self, admin: Admin) -> None:
        """Store admin in DB, ignore duplicates"""
        stmt = insert(Admin).values(admin.dict_to_insert()).on_conflict_do_nothing()

        await self._session.execute(stmt)
        await self._session.commit()

    async def set_admin_sudo(self, user_id: int, sudo: bool) -> None:
        """Set admin sudo status

        :param user_id: User telegram id
        :type user_id: int
        :param sudo: New admin sudo status
        :type sudo: bool
        """
        stmt = update(Admin).values(sudo=sudo).where(Admin.id == user_id)

        await self._session.execute(stmt)
        await self._session.commit()

    async def is_admin(self, user_id: int) -> bool:
        """Checks user is admin or not

        :param user_id: User telegram id
        :type user_id: int
        :return: User is admin boolean
        :rtype: bool
        """
        stmt = select(Admin).where(Admin.id == user_id)

        res = await self._session.execute(stmt)
        return True if res.scalar_one_or_none() else False

    async def del_admin(self, user_id: int) -> None:
        """Delete admin from DB by user id

        :param user_id: Admin telegram id
        :type user_id: int
        """
        stmt = delete(Admin).where(Admin.id == user_id)

        await self._session.execute(stmt)
        await self._session.commit()

    async def get_admin(self, user_id: int) -> Optional[Admin]:
        """Returns admin from DB by user id

        :param user_id: User telegram id
        :type user_id: int
        :return: Admin object or None if admin not exists
        :rtype: Optional[Admin]
        """
        stmt = select(Admin).where(Admin.id == user_id)

        res = await self._session.execute(stmt)
        return res.scalar_one_or_none()

    async def list_admins(self) -> Sequence[Admin]:
        """List all bot admins"""
        stmt = select(Admin).order_by(Admin.sudo.desc()).order_by(Admin.updated_on.desc())

        res = await self._session.execute(stmt)
        return res.scalars().all()
