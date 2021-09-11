__all__ = ["Process"]


from typing import Callable, Set, Union

from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from iytdl.exceptions import UnsupportedUpdateError


_CANCELLED: Set[str] = set()


class Process:
    def __init__(
        self,
        update: Union[Message, CallbackQuery],
        cb_extra: Union[int, str, None] = None,
    ) -> None:
        """
        Parameters:
        ----------
            - update (`Union[Message, CallbackQuery]`)
            - cb_extra (`Union[int, str, None]`, optional) Extra callback_data for cancel markup (default `None`)

        Raises:
        ------
            `UnsupportedUpdateError`: In case of unsupported update.
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
        self.__cb_extra = cb_extra

    @staticmethod
    def cancel_id(process_id: str) -> None:
        """Cancel Upload / Download Process by ID

        Parameters:
        ----------
            - process_id (`str`): Unique ID.

        """
        global _CANCELLED
        _CANCELLED.add(process_id)

    @staticmethod
    def remove_id(process_id: str) -> None:
        """Remove cancelled ID

        Parameters:
        ----------
            - process_id (`str`): Unique ID.

        """
        global _CANCELLED
        _CANCELLED.remove(process_id)

    @property
    def cancel(self) -> None:
        """Cancel process"""
        global _CANCELLED
        _CANCELLED.add(self.id)

    @property
    def is_cancelled(self) -> bool:
        """Check if process is cancelled

        Returns:
        -------
            - `bool`: True if cancelled else False
        """
        return self.id in _CANCELLED

    @property
    def cancel_markup(self) -> InlineKeyboardMarkup:
        cb_data = f"yt_cancel|{self.id}"
        if self.__cb_extra:
            cb_data += f"-{self.__cb_extra}"
        return InlineKeyboardMarkup(
            [[InlineKeyboardButton("❌ Cancel", callback_data=cb_data)]]
        )
