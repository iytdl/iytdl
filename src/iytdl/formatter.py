__all__ = ["ResultFormatter", "gen_search_markup"]

import json

from html import escape
from typing import Any, Dict, Union

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from iytdl.constants import *  # noqa ignore=F405


class ResultFormatter:
    def __init__(self, *args, **kwargs) -> None:
        if kwargs:
            items = kwargs.items()
        elif args:
            items = zip(
                (
                    "yt_id",
                    "thumb",
                    "title",
                    "body",
                    "duration",
                    "views",
                    "upload_date",
                    "chnl_name",
                    "chnl_id",
                ),
                args,
            )
        else:
            raise ValueError("No Input was given !")

        for key, value in items:
            setattr(self, key, value or None)

    @classmethod
    async def parse(cls, yt_class, raw_result: Dict[str, Any]) -> Dict[str, str]:
        yt_id = raw_result.get("id")
        return cls(
            yt_id=yt_id,
            # raw_result.get("thumbnails")[-1].get("url"),
            # Below thumb works everytime unlike telegra.ph or the above link.
            thumb=await yt_class.get_ytthumb(yt_id),
            title=raw_result.get("title"),
            body="".join(map(lambda x: x["text"], descripition))
            if (descripition := raw_result.get("descriptionSnippet"))
            else None,
            duration=acc.get("duration")
            if (acc := raw_result.get("accessibility"))
            else None,
            views=view.get("short") if (view := raw_result.get("viewCount")) else None,
            upload_date=raw_result.get("publishedTime"),
            chnl_name=raw_result["channel"].get("name"),
            chnl_id=raw_result["channel"].get("id"),
        ).__dict__

    @staticmethod
    def format_line(key: str, value: Union[str, int, None]) -> str:
        return f"<b>❯  {key}</b> : {value or 'N/A'}"

    @property
    def msg(self) -> str:
        out = f"<a href={YT_VID_URL}{self.yt_id}><b>{escape(self.title)}</b></a>\n"
        if self.body:
            out += f"<pre>{escape(self.body)}</pre>"
        out += "\n".join(
            map(
                lambda x: self.format_line(
                    x.replace("_", " ").title(), getattr(self, x, None)
                ),
                ("duration", "views", "upload_date"),
            )
        )
        out += "\n" + self.format_line(
            "Uploader",
            f"<a href={YT_CHANNEL_URL}{self.chnl_id}>{escape(self.chnl_name)}</a>",
        )
        return out

    def list_view(self, num: int) -> str:
        return (
            f"<img src={self.thumb}><b><a href={YT_VID_URL}{self.yt_id}>"
            f"{num}. {escape(self.title or 'N/A')}</a></b>"
        )

    def __repr__(self) -> str:
        return json.dumps(self.__dict__, indent=4)


def gen_search_markup(
    key: str, yt_id: str, total: int, page: int = 1
) -> InlineKeyboardMarkup:

    buttons = [
        [
            InlineKeyboardButton(
                text="⬅️  Back",
                callback_data=f"yt_back|{key}|{page}",
            ),
            InlineKeyboardButton(
                text=f"{page} / {total}",
                callback_data=f"yt_next|{key}|{page}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📜  List All",
                callback_data=f"yt_listall|{key}",
            ),
            InlineKeyboardButton(
                text="⬇️  Download",
                callback_data=f"yt_extract_info|{yt_id}",
            ),
        ],
    ]
    if page == 1:
        buttons[0].pop(0)
    return InlineKeyboardMarkup(buttons)
