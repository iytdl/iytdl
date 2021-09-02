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
        """
        Parameters:
        ----------
            update (`Union[Message, CallbackQuery]`)

        Raises:
        ------
            UnsupportedUpdateError: In case of unsupported update.
        """

        if not isinstance(update, (Message, CallbackQuery)):
            raise UnsupportedUpdateError

        if msg := (update if isinstance(update, Message) else update.message):
            process_id = f"{msg.chat.id}.{msg.message_id}"
            edit_func = msg.edit_text
            media_edit_func = msg.edit_media
        else:
            process_id = str(update.id)
            edit_func = update.edit_message_text
            media_edit_func = update.edit_message_media

        self.edit: Callable = edit_func
        self.edit_media: Callable = media_edit_func
        self.id: str = process_id

    @classmethod
    def cancel_id(cls, process_id: str) -> None:
        """Cancel Upload / Download Process by ID

        Parameters:
        ----------
            process_id (`str`): Unique ID.

        """
        cls.cancelled_ids.add(process_id)

    @classmethod
    def remove_id(cls, process_id: str) -> None:
        """Remove cancelled ID

        Parameters:
        ----------
            process_id (`str`): Unique ID.

        """
        cls.cancelled_ids.remove(process_id)

    @property
    def cancel(self) -> None:
        """Cancel process"""
        self.cancelled_ids.add(self.id)

    @property
    def is_cancelled(self) -> bool:
        """Check if process is cancelled

        Returns:
        -------
            bool: True if cancelled else False
        """
        return self.id in self.cancelled_ids

    @property
    def cancel_markup(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data=f"yt_cancel|{self.id}")]]
        )
