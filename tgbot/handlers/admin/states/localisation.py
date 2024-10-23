from aiogram.fsm.state import State, StatesGroup


class LocaleSG(StatesGroup):
    main = State()
    upload = State()
