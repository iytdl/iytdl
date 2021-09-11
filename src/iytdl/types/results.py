__all__ = ["SearhResult", "Buttons"]

import json

from typing import List, Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class Buttons(InlineKeyboardMarkup):
    def __init__(self, inline_keyboard: List[List["InlineKeyboardButton"]]):
        super().__init__(inline_keyboard)

    def __add__(self, extra: Union[str, int]) -> InlineKeyboardMarkup:
        """Add extra Data to callback_data of every button

        Parameters:
        ----------
            - extra (`Union[str, int]`): Extra data e.g A `key` or `user_id`.

        Raises:
        ------
            `TypeError`

        Returns:
        -------
            `InlineKeyboardMarkup`: Modified markup
        """
        if not isinstance(extra, (str, int)):
            raise TypeError(
                f"unsupported operand `extra` for + : '{type(extra)}' and '{type(self)}'"
            )
        ikb = self.inline_keyboard
        cb_extra = f"-{extra}"
        for row in ikb:
            for btn in row:
                if (
                    (cb_data := btn.callback_data)
                    and cb_data.startswith("yt_")
                    and not cb_data.endswith(cb_extra)
                ):
                    cb_data += cb_extra
                    btn.callback_data = cb_data[:64]  # limit: 1-64 bytes.
        return InlineKeyboardMarkup(ikb)

    def add(self, extra: Union[str, int]) -> InlineKeyboardMarkup:
        """Add extra Data to callback_data of every button

        Parameters:
        ----------
            - extra (`Union[str, int]`): Extra data e.g A `key` or `user_id`.

        Raises:
        ------
            `TypeError`

        Returns:
        -------
            `InlineKeyboardMarkup`: Modified markup
        """
        return self.__add__(extra)


class SearhResult:
    def __init__(
        self,
        key: str,
        text: str,
        image: str,
        buttons: InlineKeyboardMarkup,
    ) -> None:
        self.key = key
        self.buttons = Buttons(buttons.inline_keyboard)
        self.caption = text
        self.image_url = image

    def __repr__(self) -> str:
        out = self.__dict__.copy()
        out["buttons"] = (
            json.loads(str(btn)) if (btn := out.pop("buttons", None)) else None
        )
        return json.dumps(out, indent=4)
