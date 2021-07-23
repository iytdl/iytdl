__all__ = ["Downloader"]


import asyncio
import logging
import os
import time

from math import floor
from typing import Dict, Union

import youtube_dl

from pyrogram import StopPropagation
from pyrogram.errors import FloodWait
from pyrogram.types import CallbackQuery, Message
from youtube_dl.utils import DownloadError, GeoRestrictedError

from iytdl.exceptions import UnsupportedUpdateError
from iytdl.utils import *


logger = logging.getLogger(__name__)


class Downloader:
    async def video_downloader(self, url: str, uid: str, rnd_key: str, prog_func):
        options = {
            "addmetadata": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "outtmpl": os.path.join(
                str(self.download_path), rnd_key, "%(title)s-%(format)s.%(ext)s"
            ),
            "logger": logger,
            "progress_hooks": [prog_func],
            "format": uid,
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "postprocessors": [{"key": "FFmpegMetadata"}],
            "quiet": True,
            "logtostderr": False,
        }
        return await self.ytdownloader(url, options)

    async def audio_downloader(self, url: str, uid: str, rnd_key: str, prog_func):
        logger.info(f"[Seleced Audio Quality => {uid}]")
        options = {
            "outtmpl": os.path.join(
                str(self.download_path), rnd_key, "%(title)s-%(format)s.%(ext)s"
            ),
            "logger": logger,
            "progress_hooks": [prog_func],
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "format": "bestaudio/best",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": uid,
                },
                {"key": "EmbedThumbnail"},
                {"key": "FFmpegMetadata"},
            ],
            "quiet": True,
            "logtostderr": False,
        }
        return await self.ytdownloader(url, options)

    @run_sync
    def ytdownloader(self, url: str, options: Dict):
        try:
            with youtube_dl.YoutubeDL(options) as ytdl:
                out = ytdl.download([url])
        except DownloadError:
            logger.error("[DownloadError] : Failed to Download Video")
        except GeoRestrictedError:
            logger.error(
                "[GeoRestrictedError] : The uploader has not made this video"
                " available in your country"
            )
        except Exception as all_e:
            logger.error(format_exception(all_e))
        else:
            return out

    async def download(
        self,
        *args,
        downtype: str,
        update: Union[Message, CallbackQuery],
        with_progress: bool = True,
        edit_rate: int = 8,
    ):
        last_update_time = None

        if not isinstance(update, (Message, CallbackQuery)):
            raise UnsupportedUpdateError

        def prog_func(prog_data: Dict) -> None:
            nonlocal last_update_time
            now = int(time.time())
            # Only edit message once every 8 seconds to avoid ratelimits
            if prog_data.get("status") == "finished":
                progress = "🔄  Download finished, Uploading..."
            elif last_update_time is None or (now - last_update_time) >= edit_rate:
                # ------------ Progress Data ------------ #
                if not (
                    (eta := prog_data.get("eta")) and (speed := prog_data.get("speed"))
                ):
                    return
                current = prog_data.get("downloaded_bytes")
                filename = prog_data.get("filename")
                if total := prog_data.get("total_bytes"):
                    percentage = round(current / total * 100)
                    progress_bar = (
                        f"[{'█' * floor(15 * percentage / 100)}"
                        f"{'░' * floor(15 * (1 - percentage / 100))}]"
                    )
                    # ---------------------------------------- #
                    progress = f"""
<i>Downloading:</i>  <code>{filename}</code>
<b>Completed:</b>  <code>{humanbytes(current)} / {humanbytes(total)}</code>
<b>Progress:</b>  <code>{progress_bar} {percentage} %</code>
<b>Speed:</b>  <code>{humanbytes(speed)}</code>
<b>ETA:</b>  <code>{time_formater(eta)}</code>
"""
                else:
                    # Total is None, Generic progress bar
                    progress = f"""
<i>Downloading:</i>  <code>{filename}</code>
<b>Completed:</b>  <code>{humanbytes(current)} / [N/A]</code>
<b>Speed:</b>  <code>-</code>
<b>ETA:</b>  <code>-</code>
"""
            else:
                return
            if with_progress:
                self.loop.create_task(self.progress_func(update, progress))
            last_update_time = now

        if downtype == "video":
            return await self.video_downloader(*args, prog_func)
        elif downtype == "audio":
            return await self.audio_downloader(*args, prog_func)
        else:
            raise TypeError(f"'{downtype}' is Unsupported !")

    @staticmethod
    async def progress_func(update: Union[Message, CallbackQuery], text: str) -> None:
        try:
            edit = (
                update.edit_text
                if isinstance(update, Message)
                else update.edit_message_text
            )
            await edit(
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=None,
            )
        except FloodWait as f:
            await asyncio.sleep(f.x)
        except StopPropagation:
            raise StopPropagation
        except Exception as e:
            logger.error(format_exception(e))
