from aiogram.fsm.state import State, StatesGroup


class BroadcastSG(StatesGroup):
    main = State()
    media = State()
    text = State()
    link = State()
    preview = State()
