__all__ = ["SearhResult"]

import json

from typing import Optional

from pyrogram.types import InlineKeyboardMarkup


class SearhResult:
    key: str
    buttons: Optional[InlineKeyboardMarkup]
    text: str
    image: str

    def __init__(
        self,
        key: str,
        text: str,
        image: str,
        buttons: Optional[InlineKeyboardMarkup] = None,
    ) -> None:
        self.key = key
        self.buttons = buttons
        self.caption = text
        self.image_url = image

    def __repr__(self):
        return json.dumps(self.__dict__, indent=4)
