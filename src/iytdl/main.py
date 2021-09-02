__all__ = ["iYTDL"]

import asyncio
import hashlib
import re

from pathlib import Path
from typing import Optional, Tuple, Union

from aiohttp import ClientSession
from html_telegraph_poster import TelegraphPoster
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from youtubesearchpython.__future__ import VideosSearch

from iytdl import types
from iytdl.constants import YT_VID_URL
from iytdl.downloader import Downloader
from iytdl.exceptions import *  # noqa ignore=F405
from iytdl.extractors import Extractor
from iytdl.formatter import ResultFormatter, gen_search_markup
from iytdl.sql_cache import AioSQLiteDB
from iytdl.upload_lib.uploader import Uploader
from iytdl.utils import run_sync


class iYTDL(Extractor, Downloader, Uploader):
    def __init__(
        self,
        log_group_id: Union[int, str],
        session: Optional[ClientSession] = None,
        silent: bool = False,
        download_path: str = "downloads",
        loop: Optional[asyncio.AbstractEventLoop] = None,
        default_thumb: str = "https://i.imgur.com/4LwPLai.png",
        cache_path: str = "",
        delete_media: bool = False,
        external_downloader: Optional[types.ExternalDownloader] = None,
    ) -> None:
        """Main Class

        Parameters:
        ----------
            - log_group_id (`Union[int, str]`):  Log channel / group id to upload downloaded media.
            - session (`Optional[ClientSession]`, optional): Aiohttp ClientSession. (Defaults to `None`)
            - silent (`bool`, optional): Disable youtube_dl stdout. (Defaults to `False`)
            - download_path (`str`, optional): Custom download location. (Defaults to `"downloads"`)
            - loop (`Optional[asyncio.AbstractEventLoop]`, optional): Event loop. (Defaults to `None`)
            - default_thumb (`str`, optional): Fallback thumbnail. (Defaults to `"https://i.imgur.com/4LwPLai.png"`)
            - cache_path (`str`, optional): Path to store cache. (Defaults to `""`)
            - delete_media: (`bool`, optional): Delete media from local storage after uploading on Telegram. (Defaults to `False`)
            - external_downloader: (`Optional[types.ExternalDownloader]`, optional): External Downloader e.g `types.external_downloader.Aria2c`. (Defaults to `None`)
        """
        self.yt_link_regex = re.compile(
            r"(?:youtube\.com|youtu\.be)/(?:[\w-]+\?v=|embed/|v/|shorts/)?([\w-]{11})"
        )
        self.generic_url_regex = re.compile(r"^https?://\S+")
        self.default_thumb = default_thumb
        self.http = session or ClientSession()
        _cache_path = Path(cache_path)
        if _cache_path.is_file():
            raise TypeError(f"'{cache_path}' expected a Directory got a File instead")
        self.cache = AioSQLiteDB(
            _cache_path.joinpath("yt_search_cache.db"), clean=False
        )
        self.loop = loop or asyncio.get_event_loop()
        self.download_path = Path(download_path)
        self.log_group_id = log_group_id

        self.download_path.mkdir(exist_ok=True, parents=True)
        self.external_downloader = external_downloader
        self.delete_file_after_upload = delete_media

        super().__init__(silent=silent)

    @classmethod
    async def init(cls, *args, **kwargs) -> "iYTDL":
        yt = cls(*args, **kwargs)
        await yt.start()
        return yt

    async def search(self, query: str) -> types.SearhResult:
        """Search

        Parameters:
        ----------
            - query (`str`): Provide URL or text.

        Raises:
        ------
            `NoResultFoundError`: In case of no result.

        Returns:
        -------
            `types.SearhResult`
        """
        hash_key = hashlib.sha1(query.encode(encoding="UTF-8")).hexdigest()
        # sqlite doesn't support numbers in table name
        key = re.sub(r"\d+", "", hash_key)[:10]
        if cached_data := await self.cache.get_key(key, index=0):
            s_len, v_data = cached_data
        else:
            videosResult = await VideosSearch(query, limit=15).next()
            if len((res := videosResult["result"])) == 0:
                raise NoResultFoundError
            search_data = await asyncio.gather(
                *map(lambda x: ResultFormatter.parse(self, x), res[:15])
            )
            await self.cache.set_key(key, search_data)
            v_data = search_data[0]
            s_len = len(search_data)
        r1 = ResultFormatter(**v_data)
        return types.SearhResult(
            key, r1.msg, r1.thumb, gen_search_markup(key, r1.yt_id, s_len)
        )

    async def next_result(self, key: str, index: int) -> types.SearhResult:
        """Get next result from cached data

        Parameters:
        ----------
            - key (`str`): Unique Key.
            - index (`int`): Result Index.

        Returns:
        -------
            `types.SearhResult`
        """
        if cached_data := await self.cache.get_key(key, index=index - 1):
            s_len, v_data = cached_data
            vid = ResultFormatter(**v_data)
            return types.SearhResult(
                key,
                vid.msg,
                vid.thumb,
                gen_search_markup(key, vid.yt_id, s_len, index),
            )

    async def extract_info_from_key(self, key: str) -> Optional[types.SearhResult]:
        """
        Parameters:
        ----------
            - key (`str`): Unique Key.

        Returns:
        -------
            `Optional[types.SearhResult]`: If key exist in cache.
        """
        if len(key) == 11:
            # yt_id
            return await self.get_download_button(key)
        if url := await self.cache.get_url(key):
            return await self.generic_extractor(key, url)

    async def parse(self, search_query: str, extract: bool = True) -> types.SearhResult:
        """Automatically parses `search_query`.

        Parameters:
        ----------
            - search_query (`str`): accepts [Youtube URL | URL | Text].
            - extract (`bool`, optional): Extract Information (Defaults to `True`)

        Raises:
        ------
            `NoResultFoundError`: In case of no result.

        Returns:
        -------
            `types.SearhResult`
        """
        query_split = search_query.split()
        if len(query_split) == 1:
            url = query_split[0]
            # can be some text or an URL
            if match := self.yt_link_regex.search(url):
                # youtube link
                yt_id = match.group(1)
                thumb = await self.get_ytthumb(yt_id)
                if extract:
                    return await self.get_download_button(yt_id)
                return types.SearhResult(
                    yt_id,
                    f"**[YouTube URL]** -> `'{YT_VID_URL}{yt_id}'`",
                    thumb,
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "⚙️ Extract Info",
                                    callback_data=f"yt_extract_info|{yt_id}",
                                )
                            ]
                        ]
                    ),
                )
            elif self.generic_url_regex.search(url):
                # Matches URL regex that can be supported by YoutubeDL
                key = await self.cache.save_url(url)
                if extract:
                    return await self.generic_extractor(key, url)

                return types.SearhResult(
                    key,
                    f"**[Generic URL]** -> `'{url}'`",
                    self.default_thumb,
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "⚙️ Extract Info",
                                    callback_data=f"yt_extract_info|{key}",
                                )
                            ]
                        ]
                    ),
                )
        # YT Search if query didn't matched earlier or is of multiple words
        return await self.search(search_query.strip())

    async def listview(self, key: str) -> Tuple[InputMediaPhoto, InlineKeyboardMarkup]:
        """List data on Telegra.ph

        Parameters:
        ----------
            - key (`str`): Unique Key.

        Returns:
        -------
            `Tuple[InputMediaPhoto, InlineKeyboardMarkup]`
        """
        if cached_data := await self.cache.get_key(key):
            content = "\n".join(
                map(
                    lambda x: ResultFormatter(*x[1]).list_view(x[0]),
                    enumerate(cached_data, start=1),
                )
            )
            telegraph = await self.paste_to_tg("📜  LIST VIEW", content)
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "↗️  Click To Open",
                            url=telegraph,
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📰  Detailed View",
                            callback_data=f"yt_next|{key}|0",
                        )
                    ],
                ]
            )
            image = ResultFormatter(*cached_data[0]).thumb
            return InputMediaPhoto(media=image), buttons

    @staticmethod
    async def paste_to_tg(title: str, content: str) -> str:
        """Paste to Telegra.ph

        Parameters:
        ----------
            - title (`str`): Page title.
            - content (`str`): Page content.

        Returns:
        -------
            `str`: Telegra.ph URL
        """
        post_client = TelegraphPoster(use_api=True)
        auth_name = "X"
        post_client.create_api_token(auth_name)
        return (
            await run_sync(post_client.post)(
                title=title,
                author=auth_name,
                author_url="https://t.me/x_xtests",
                text=content,
            )
        ).get("url")

    async def get_ytthumb(self, yt_id: str) -> str:
        """Get YouTube video thumbnail from video ID

        Parameters:
        ----------
            - yt_id (`str`): YouTube video ID.

        Returns:
        -------
            `str`: Thumbnail URL
        """
        for quality in (
            "maxresdefault",
            "hqdefault",
            "sddefault",
            "mqdefault",
            "default",
        ):
            link = f"https://i.ytimg.com/vi/{yt_id}/{quality}.jpg"
            async with self.http.get(link) as resp:
                if resp.status == 200:
                    break
        else:
            link = self.default_thumb
        return link

    async def stop(self) -> None:
        """Stop iYTDL instance manually or Use Context Manager"""
        if self.http and not self.http.closed:
            await self.http.close()
        await self.cache.close()

    async def start(self) -> None:
        """Start iYTDL instance manually or Use Context Manager"""
        await self.cache._init()

    async def __aenter__(self) -> "iYTDL":
        await self.start()
        return self

    async def __aexit__(self, *_, **__) -> None:
        await self.stop()
