from aiogram.fsm.state import State, StatesGroup


class UserSG(StatesGroup):
    lst = State()


class ProfileUserSG(StatesGroup):
    profile = State()
