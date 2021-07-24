__all__ = ["Process"]

from typing import Callable, Set, Union

from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from iytdl.exceptions import UnsupportedUpdateError


class Process:
    cancelled_ids: Set[str] = set()

    def __init__(self, update: Union[Message, CallbackQuery]) -> None:

        if not isinstance(update, (Message, CallbackQuery)):
            raise UnsupportedUpdateError

        if msg := (update if isinstance(update, Message) else update.message):
            process_id = f"{msg.chat.id}.{msg.message_id}"
            edit_func = msg.edit_text
        else:
            process_id = str(update.id)
            edit_func = update.edit_message_text

        self.has_msg: bool = bool(msg)
        self.edit: Callable = edit_func
        self.id: str = process_id

    @property
    def is_cancelled(self) -> bool:
        return self.id in self.cancelled_ids

    @property
    def cancel(self) -> None:
        self.cancelled_ids.add(self.id)

    @property
    def cancel_markup(self) -> InlineKeyboardMarkup:
        delete = self.has_msg
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "❌ Cancel", callback_data=f"yt_cancell|{self.id}|{delete}"
                    )
                ]
            ]
        )
