__all__ = ["SearhResult"]

import json

from pyrogram.types import InlineKeyboardMarkup


class SearhResult:
    key: str
    buttons: InlineKeyboardMarkup
    text: str
    image: str

    def __init__(
        self,
        key: str,
        text: str,
        image: str,
        buttons: InlineKeyboardMarkup,
    ) -> None:
        self.key = key
        self.buttons = buttons
        self.caption = text
        self.image_url = image

    def __repr__(self) -> str:
        out = self.__dict__.copy()
        out["buttons"] = (
            json.loads(str(btn)) if (btn := out.pop("buttons", None)) else None
        )
        return json.dumps(out, indent=4)
