__all__ = ["Uploader"]

import asyncio
import logging
import os

from shutil import rmtree
from typing import Any, Dict, Literal, Optional, Union

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram import Client
from pyrogram.types import (
    CallbackQuery,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaVideo,
    Message,
)

from iytdl.processes import Process
from iytdl.upload_lib import ext
from iytdl.upload_lib.functions import covert_to_jpg, thumb_from_audio, unquote_filename
from iytdl.upload_lib.progress import progress as upload_progress
from iytdl.utils import *  # noqa ignore=F405


logger = logging.getLogger(__name__)


class Uploader:
    @run_sync
    def find_media(
        self, key: str, media_type: Literal["audio", "video"]
    ) -> Dict[str, Any]:
        """Search Downloaded files for thumbnail and media

        Parameters:
        ----------
            - key (`str`): Unique Key i.e Subfolder name.
            - media_type (`Literal['audio', 'video']`).

        Raises:
        ------
            `TypeError`: In case of Invalid 'media_type'
            `FileNotFoundError`: If Subfolder doesn't exists

        Returns:
        -------
            `Dict[str, Any]`
        """
        if media_type not in ("video", "audio"):
            raise TypeError("'media_type' only accepts video or audio")
        media_path = self.download_path.joinpath(key)
        if not media_path.is_dir():
            raise FileNotFoundError(f"'{media_path}' doesn't exist !")
        info_dict: Dict = {}
        for file in media_path.iterdir():
            if (
                not info_dict.get(media_type)
                and file.name.lower().endswith(getattr(ext, media_type))
                and file.stat().st_size != 0
            ):
                if (
                    file.stat().st_size > 2147000000
                ):  # 2 * 1024 * 1024 * 1024 = 2147483648
                    raise ValueError(
                        f"[{file}] will not be uploaded as filesize exceeds '2 GB' !"
                    )
                f_path = unquote_filename(file)
                info_dict[media_type] = f_path
                info_dict["file_name"] = os.path.basename(f_path)
            if not info_dict.get("thumb") and file.name.lower().endswith(ext.photo):
                info_dict["thumb"], info_dict["size"] = covert_to_jpg(file)

            if media_type in info_dict and "thumb" in info_dict:
                break

        if media := info_dict.get(media_type):
            metadata = extractMetadata(createParser(media))
            if metadata and metadata.has("duration"):
                info_dict["duration"] = metadata.get("duration").seconds

            if media_type == "audio":
                info_dict.pop("size", None)
                if metadata.has("artist"):
                    info_dict["performer"] = metadata.get("artist")
                if metadata.has("title"):
                    info_dict["title"] = metadata.get("title")
                # If Thumb doesn't exist then check for Album art
                if not info_dict.get("thumb"):
                    info_dict["thumb"] = thumb_from_audio(media)
            else:
                width, height = info_dict.pop("size", (1280, 720))
                info_dict["height"] = height
                info_dict["width"] = width
            return info_dict

    async def get_input_media(
        self,
        key: str,
        media_type: Literal["audio", "video"],
        caption: str,
        parse_mode: Optional[str] = "HTML",
    ) -> Union[InputMediaAudio, InputMediaVideo, None]:
        """Get Input Media

        Parameters:
        ----------
            - key (`str`): Unique Key.
            - media_type (`Literal['audio', 'video']`): audio or video.
            - caption (`str`): Media caption text.
            - parse_mode (`Optional[str]`, optional):
                By default, texts are parsed using both Markdown and HTML styles.
                You can combine both syntaxes together.
                Pass "markdown" or "md" to enable Markdown-style parsing only.
                Pass "html" to enable HTML-style parsing only.
                Pass None to completely disable style parsing. (Defaults to `"HTML"`)

        Returns:
        -------
            `Union[InputMediaAudio, InputMediaVideo, None]`
        """
        if media_kwargs := await self.find_media(key, media_type):
            media_kwargs.update(
                {
                    "media": media_kwargs.pop(media_type),
                    "caption": caption,
                    "parse_mode": parse_mode,
                }
            )
            if media_type == "audio":
                return InputMediaAudio(**media_kwargs)
            if media_type == "video":
                return InputMediaVideo(**media_kwargs)

    async def upload(
        self,
        client: Client,
        key: str,
        downtype: str,
        update: Union[CallbackQuery, Message],
        caption_link: Optional[str] = None,
        with_progress: bool = True,
    ) -> Union[CallbackQuery, Message]:
        """Upload downloaded Media with progress

        Parameters:
        ----------
            - client (`Client`): Pyrogram Bot Client.
            - key (`str`): Unique key to find downloaded media.
            - downtype (`str`): (`Literal['audio', 'video']`).
            - update (`Union[CallbackQuery, Message]`): Pyrogram Update to edit message.
            - caption_link (`Optional[str]`, optional): Custom caption href link. (Defaults to `None`)
            - with_progress (`bool`, optional): Enable / Disable progress. (Defaults to `True`)

        Returns:
        -------
            `Union[CallbackQuery, Message]`: On Success
        """
        if mkwargs := await self.find_media(key, downtype):

            if caption_link:
                caption = f"<b><a href={caption_link}>{mkwargs['file_name']}</a></b>"
            else:
                caption = f"<b>{mkwargs['file_name']}</b>"
            process = Process(update)
            try:
                if downtype == "video":
                    return await self.__upload_video(
                        client, process, caption, mkwargs, with_progress
                    )
                if downtype == "audio":
                    return await self.__upload_audio(
                        client, process, caption, mkwargs, with_progress
                    )
            finally:
                if self.delete_file_after_upload:
                    rmtree(self.download_path.joinpath(key), ignore_errors=True)

    async def __upload_video(
        self,
        client: Client,
        process: Process,
        caption: str,
        mkwargs: Dict[str, Any],
        with_progress: bool = True,
    ):

        if not mkwargs.get("thumb") and (duration := mkwargs.get("duration")):
            ttl = duration // 2

            mkwargs["thumb"] = await take_screen_shot(mkwargs["video"], ttl)

        if not (
            uploaded := await client.send_video(
                chat_id=self.log_group_id,
                caption=f"📹  {caption}",
                parse_mode="HTML",
                disable_notification=True,
                progress=upload_progress if with_progress else None,
                progress_args=(client, process, mkwargs["file_name"])
                if with_progress
                else (),
                **mkwargs,
            )
        ):

            return
        await asyncio.sleep(2)
        if not process.is_cancelled:
            if uploaded.video:

                return await process.edit_media(
                    media=InputMediaVideo(
                        uploaded.video.file_id, caption=uploaded.caption.html
                    ),
                    reply_markup=None,
                )
            elif uploaded.document:
                return await process.edit_media(
                    media=InputMediaDocument(
                        uploaded.document.file_id, caption=uploaded.caption.html
                    ),
                    reply_markup=None,
                )

    async def __upload_audio(
        self,
        client: Client,
        process: Process,
        caption: str,
        mkwargs: Dict[str, Any],
        with_progress: bool = True,
    ):
        if not (
            uploaded := await client.send_audio(
                chat_id=self.log_group_id,
                caption=f"🎵  {caption}",
                parse_mode="HTML",
                disable_notification=True,
                progress=upload_progress if with_progress else None,
                progress_args=(client, process, mkwargs["file_name"])
                if with_progress
                else (),
                **mkwargs,
            )
        ):
            return
        await asyncio.sleep(2)
        if not process.is_cancelled:
            if uploaded.audio:
                return await process.edit_media(
                    media=InputMediaAudio(
                        uploaded.audio.file_id, caption=uploaded.caption.html
                    ),
                    reply_markup=None,
                )
            elif uploaded.document:
                return await process.edit_media(
                    media=InputMediaDocument(
                        uploaded.document.file_id, caption=uploaded.caption.html
                    ),
                    reply_markup=None,
                )
