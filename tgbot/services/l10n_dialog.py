from typing import Any, Dict, Protocol

from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.text import Text


class Values(Protocol):
    def __getitem__(self, item: Any) -> Any:
        raise NotImplementedError


class L10NFormat(Text):
    def __init__(self, text: str, when: WhenCondition = None):
        super().__init__(when)
        self.text = text

    async def _render_text(self, data: Dict, manager: DialogManager) -> str:
        l10n = manager.middleware_data.get("l10n")
        return l10n.format_value(self.text, data)
