from aiogram.fsm.state import State, StatesGroup


class AudioSG(StatesGroup):
    artist = State()
    title = State()
    album = State()
    cover = State()
    preview = State()
