__all__ = ["_PROCESS", "Uploader"]

import asyncio
import logging
import os
import re
import time
from io import BytesIO
from math import floor
from pathlib import Path, PurePath
from typing import Any, Callable, Dict, Optional, Tuple, Union

import mutagen
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image
from pyrogram import Client, StopPropagation
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaAudio, InputMediaVideo
from pyrogram.types.bots_and_keyboards.callback_query import CallbackQuery
from pyrogram.types.messages_and_media.message import Message

from iytdl.utils import *  # noqa ignore=F405

logger = logging.getLogger(__name__)
_PROCESS: Dict[str, Tuple[int, int]] = {}


async def upload_progress(
    current: int,
    total: int,
    update: Union[Message, CallbackQuery],
    filename: str,
    mode: str = "upload",
    edit_rate: int = 8,
):
    if update.message:
        edit_func = update.edit_text
        process_id = f"{update.message.chat.id}.{update.message.message_id}"
    else:
        edit_func = update.edit_message_text
        process_id = update.id
    if current == total:
        try:
            await edit_func(f"`finalizing {mode} process ...`")
        except FloodWait as f_w:
            await asyncio.sleep(f_w.x)
        return
    now = int(time.time())
    if process_id not in _PROCESS:
        _PROCESS[process_id] = (now, now)
    start, last_update_time = _PROCESS[process_id]
    # ------------------------------------ #
    if (now - last_update_time) >= edit_rate:
        _PROCESS[process_id] = (start, now)
        # Only edit message once every 8 seconds to avoid ratelimits
        after = now - start
        speed = current / after
        eta = round((total - current) / speed)
        percentage = round(current / total * 100)
        progress_bar = (
            f"[{'█' * floor(15 * percentage / 100)}"
            f"{'░' * floor(15 * (1 - percentage / 100))}]"
        )
        progress = f"""
<i>{mode.title()}ing:</i>  <code>{filename}</code>
<b>Completed:</b>  <code>{humanbytes(current)} / {humanbytes(total)}</code>
<b>Progress:</b>  <code>{progress_bar} {percentage} %</code>
<b>Speed:</b>  <code>{humanbytes(speed)}</code>
<b>ETA:</b>  <code>{time_formater(eta)}</code>
"""
        try:
            await edit_func(progress, reply_markup=None)
        except FloodWait as f:
            await asyncio.sleep(f.x)
        except StopPropagation:
            raise StopPropagation
        except Exception as e:
            logger.error(format_exception(e))


class Ext:
    audio = (".mp3", ".flac", ".wav", ".m4a")
    video = (".mkv", ".mp4", ".webm")
    thumb = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


class Uploader:
    @run_sync
    def find_media(
        self, key: str, media_type: str = "video"
    ) -> Dict[str, Union[str, Tuple, None]]:
        if media_type not in ("video", "audio"):
            raise TypeError("'media_type' only accepts video or audio")
        media_path = self.download_path.joinpath(key)
        if not media_path.is_dir():
            # Check if download dir exist
            raise FileNotFoundError(f"'{media_path}' doesn't exist !")
        info_dict = {}
        for file in media_path.iterdir():
            # Find Media
            if (
                not info_dict.get(media_type)
                and file.name.lower().endswith(getattr(Ext, media_type))
                and file.stat().st_size != 0
            ):
                f_path = self.unquote_filename(file)
                info_dict[media_type] = f_path
                info_dict["file_name"] = os.path.basename(f_path)
            # Find thumbnail
            if not info_dict.get("thumb") and file.name.lower().endswith(Ext.thumb):
                with Image.open(file) as im:
                    if not file.name.lower().endswith(Ext.thumb[:2]):
                        thumb_path = str(media_path.joinpath(f"{file.stem}.jpeg"))
                        im.convert("RGB").save(thumb_path, "JPEG")
                    else:
                        thumb_path = str(file)
                    info_dict["size"] = im.size
                    info_dict["thumb"] = thumb_path
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
                    audio_id3 = mutagen.File(media)
                    for k in audio_id3.keys():
                        if "APIC" in k:
                            if album_art := getattr(audio_id3[k], "data", None):
                                thumb_path = str(media_path.joinpath("album_art.jpg"))
                                with Image.open(BytesIO(album_art)) as im:
                                    im.convert("RGB").save(thumb_path, "JPEG")
                                info_dict["thumb"] = thumb_path
                            break
            else:
                width, height = info_dict.pop("size", (1280, 720))
                info_dict["height"] = height
                info_dict["width"] = width
            return info_dict

    async def get_input_media(
        self,
        key: str,
        media_type: str,
        caption: str,
        parse_mode: Optional[str] = "HTML",
    ) -> Union[InputMediaAudio, InputMediaVideo, None]:
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

    @staticmethod
    def unquote_filename(filename: Union[PurePath, str]) -> str:
        file = Path(filename) if isinstance(filename, str) else filename
        un_quoted = file.parent.joinpath(re.sub(r"[\"']", "", file.name))
        if file.name != un_quoted.name:
            file.rename(un_quoted)
            return str(un_quoted)
        return str(filename)

    async def upload(
        self,
        client: Client,
        rnd_id: str,
        downtype: str,
        update: Union[CallbackQuery, Message],
        link: Optional[str] = None,
    ):
        if mkwargs := await self.find_media(rnd_id, downtype):
            if link:
                caption = f"<b><a href={link}>{mkwargs['file_name']}</a></b>"
            else:
                caption = f"<b>{mkwargs['file_name']}</b>"
            edit_func = (
                update.edit_media
                if isinstance(update, Message)
                else update.edit_message_media
            )
            if downtype == "video":
                await self.__upload_video(client, update, caption, mkwargs, edit_func)
            if downtype == "audio":
                await self.__upload_audio(client, update, caption, mkwargs, edit_func)

    async def __upload_video(
        self,
        client: Client,
        update: Union[CallbackQuery, Message],
        caption: str,
        mkwargs: Dict[str, Any],
        edit_func: Callable,
    ):
        uploaded = await client.send_video(
            chat_id=self.log_group_id,
            caption=f"📹  {caption}",
            parse_mode="HTML",
            disable_notification=True,
            progress=upload_progress,
            progress_args=(update, mkwargs["file_name"]),
            **mkwargs,
        )
        if uploaded.video:
            await edit_func(
                media=InputMediaVideo(
                    uploaded.video.file_id, caption=uploaded.caption.html
                ),
                reply_markup=None,
            )

    async def __upload_audio(
        self,
        client: Client,
        update: Union[CallbackQuery, Message],
        caption: str,
        mkwargs: Dict[str, Any],
        edit_func: Callable,
    ):
        uploaded = await client.send_audio(
            chat_id=self.log_group_id,
            caption=f"🎵  {caption}",
            parse_mode="HTML",
            disable_notification=True,
            progress=upload_progress,
            progress_args=(update, mkwargs["file_name"]),
            **mkwargs,
        )
        if uploaded.audio:
            await edit_func(
                media=InputMediaAudio(
                    uploaded.audio.file_id, caption=uploaded.caption.html
                ),
                reply_markup=None,
            )
