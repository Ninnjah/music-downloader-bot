import logging
from operator import itemgetter

from aiogram import F, Router
from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from aiogram_dialog.widgets.common import ManagedScroll
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (
    Back,
    Button,
    Cancel,
    Group,
    ListGroup,
    Next,
    NumberedPager,
    Row,
    StubScroll,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format
from fluent.runtime import FluentLocalization

from tgbot.handlers.admin.states.broadcast import BroadcastSG
from tgbot.keyboard.inline import url_kb
from tgbot.models.album import INPUT_TYPES, Album
from tgbot.services.broadcaster import broadcast
from tgbot.services.broadcaster import send_message as preview_message
from tgbot.services.l10n_dialog import L10NFormat
from tgbot.services.repository import Repo
# TODO FULL REWRITE
# TODO SWITCH TO aiogram-broadcast or taskiq

logger = logging.getLogger(__name__)
router = Router(name=__name__)
PREVIEW_STATE = BroadcastSG.preview
FINISHED_KEY = "finished"
CANCEL_EDIT = SwitchTo(
    L10NFormat("admin-button-cancel-edit"),
    when=F["dialog_data"][FINISHED_KEY],
    id="cnl_edt",
    state=PREVIEW_STATE,
)


async def next_or_end(event, widget, dialog_manager: DialogManager, *_):
    if dialog_manager.dialog_data.get(FINISHED_KEY):
        await dialog_manager.switch_to(PREVIEW_STATE)
    else:
        await dialog_manager.next()


async def load_message(dialog_manager: DialogManager, **kwargs):
    scroll: ManagedScroll = dialog_manager.find("pages")
    media_number = await scroll.get_page()

    media_list = dialog_manager.dialog_data.get("media", [])
    if not media_list:
        media = None
    else:
        media = media_list[media_number]
        media = MediaAttachment(type=media[0], file_id=MediaId(media[1]))

    return {
        "media_count": len(media_list),
        "media_number": media_number + 1,
        "media": media,
        "text": dialog_manager.dialog_data.get("text"),
        "link_list": dialog_manager.dialog_data.get("link_list", []),
    }


async def result_getter(dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog_data[FINISHED_KEY] = True
    return await load_message(dialog_manager)


async def get_destination(dialog_manager: DialogManager, l10n: FluentLocalization, **kwargs):
    return {
        "destination": [
            ("all", l10n.format_value("admin-message-all")),
            ("client", l10n.format_value("admin-message-client")),
            ("performer", l10n.format_value("admin-message-performer")),
        ]
    }


async def post_handler(m: Message, msg_input: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data["text"] = m.html_text
    await next_or_end(m, msg_input, dialog_manager)


async def post_media_handler(m: Message, msg_input: MessageInput, dialog_manager: DialogManager):
    album: Album = dialog_manager.middleware_data["album"]
    dialog_manager.dialog_data["media"] = [(media.type, media.media) for media in album.as_media_group]
    await next_or_end(m, msg_input, dialog_manager)


async def post_link_handler(m: Message, msg_input: MessageInput, dialog_manager: DialogManager):
    url_list = []
    entities = m.entities or []
    for entity in entities:
        if entity.type == "url":
            url_list.append(entity.extract_from(m.text))

    link_list = []
    for line in m.text.split("\n"):
        data = line.split(":", maxsplit=1)
        if len(data) < 2:
            continue

        text, url = (data[0].strip(), data[1].strip())
        if url in url_list:
            link_list.append((text, url))

    dialog_manager.dialog_data["link_list"] = link_list
    await next_or_end(m, msg_input, dialog_manager)


async def post_link_empty_handler(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    dialog_manager.dialog_data["link_list"] = []


async def send_preview(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    media_list = dialog_manager.dialog_data.get("media", [])
    text = dialog_manager.dialog_data.get("text")
    link_list = dialog_manager.dialog_data.get("link_list")
    reply_markup = url_kb.get(link_list) if link_list else None

    if media_list:
        media_group = [
            INPUT_TYPES[media[0]](
                type=media[0],
                media=media[1],
                caption=text if i == 0 else None,
            )
            for i, media in enumerate(media_list)
        ]
        text = None
    else:
        media_group = None
        text = text

    await preview_message(
        bot=callback.bot,
        user_id=callback.from_user.id,
        text=text,
        media_group=media_group,
        reply_markup=reply_markup,
    )


async def send_message(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    repo: Repo = dialog_manager.middleware_data["repo"]
    l10n: FluentLocalization = dialog_manager.middleware_data["l10n"]

    user_list = [user.id for user in await repo.list_users()]
    media_list = dialog_manager.dialog_data.get("media", [])
    text = dialog_manager.dialog_data.get("text")
    link_list = dialog_manager.dialog_data.get("link_list")
    reply_markup = url_kb.get(link_list) if link_list else None

    if media_list:
        media_group = [
            INPUT_TYPES[media[0]](
                type=media[0],
                media=media[1],
                caption=text if i == 0 else None,
            )
            for i, media in enumerate(media_list)
        ]
        text = None
    else:
        media_group = None
        text = text

    total_count = len(user_list)

    sent_count = await broadcast(
        bot=callback.bot,
        users=user_list,
        text=text,
        media_group=media_group,
        reply_markup=reply_markup,
    )

    await callback.message.answer(
        l10n.format_value(
            "admin-messages-sent",
            dict(total_count=total_count, sent_count=sent_count),
        )
    )
    await dialog_manager.done()


post_dialog = Dialog(
    Window(
        L10NFormat("admin-message-media-text-ask"),
        MessageInput(
            post_media_handler,
            content_types=[ContentType.PHOTO, ContentType.VIDEO],
        ),
        SwitchTo(L10NFormat("admin-button-skip"), id="media_skip", state=BroadcastSG.text),
        CANCEL_EDIT,
        Cancel(L10NFormat("admin-button-cancel")),
        state=BroadcastSG.main,
    ),
    Window(
        L10NFormat("admin-message-media-preview-text"),
        DynamicMedia(selector="media"),
        StubScroll(id="pages", pages="media_count"),
        Group(
            NumberedPager(scroll="pages", when=F["pages"] > 1),
            width=8,
        ),
        MessageInput(
            content_types=[ContentType.PHOTO, ContentType.VIDEO],
            func=post_media_handler,
        ),
        Row(
            Back(L10NFormat("admin-button-send-again")),
            Next(L10NFormat("admin-button-next")),
        ),
        CANCEL_EDIT,
        Cancel(L10NFormat("admin-button-cancel")),
        state=BroadcastSG.media,
        getter=load_message,
    ),
    Window(
        L10NFormat("admin-message-text-ask"),
        MessageInput(
            post_handler,
            content_types=[ContentType.TEXT],
        ),
        CANCEL_EDIT,
        Cancel(L10NFormat("admin-button-cancel")),
        state=BroadcastSG.text,
    ),
    Window(
        L10NFormat("admin-message-link-ask"),
        MessageInput(
            post_link_handler,
            content_types=[ContentType.TEXT],
        ),
        Next(
            L10NFormat("admin-button-skip"),
            on_click=post_link_empty_handler,
        ),
        CANCEL_EDIT,
        Cancel(L10NFormat("admin-button-cancel")),
        state=BroadcastSG.link,
    ),
    Window(
        L10NFormat("admin-message-preview-text"),
        DynamicMedia(selector="media"),
        StubScroll(id="pages", pages="media_count"),
        Group(NumberedPager(scroll="pages", when=F["pages"] > 1), width=8),
        ListGroup(
            Url(Format("{item[0]}"), Format("{item[1]}")),
            id="link_list",
            item_id_getter=itemgetter(1),
            items="link_list",
        ),
        MessageInput(
            content_types=[ContentType.PHOTO, ContentType.VIDEO],
            func=post_media_handler,
        ),
        SwitchTo(
            L10NFormat("admin-message-edit-media"),
            state=BroadcastSG.main,
            id="to_media",
        ),
        SwitchTo(
            L10NFormat("admin-message-edit-text"),
            state=BroadcastSG.text,
            id="to_text",
        ),
        SwitchTo(
            L10NFormat("admin-message-edit-link"),
            state=BroadcastSG.link,
            id="to_link",
        ),
        Button(
            L10NFormat("admin-button-send-preview"),
            id="message_preview",
            on_click=send_preview,
        ),
        Button(
            L10NFormat("admin-button-send"),
            id="message_send",
            on_click=send_message,
        ),
        Cancel(L10NFormat("admin-button-cancel")),
        state=BroadcastSG.preview,
        getter=result_getter,
    ),
)


router.include_routers(
    post_dialog,
)
