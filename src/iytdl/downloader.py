__all__ = ["Downloader"]


import asyncio
import logging
import os
import time

from math import floor
from typing import Any, Callable, Dict, Union

import yt_dlp as youtube_dl

from pyrogram import ContinuePropagation, StopPropagation, StopTransmission
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import CallbackQuery, Message

# from youtube_dl.utils import DownloadError, GeoRestrictedError
from yt_dlp.utils import DownloadError, GeoRestrictedError

from iytdl.processes import Process
from iytdl.utils import *


logger = logging.getLogger(__name__)


class Downloader:
    async def video_downloader(
        self, url: str, uid: str, rnd_key: str, prog_func: Callable
    ) -> Union[int, str]:

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
            "quiet": self.silent,
            "logtostderr": self.silent,
        }

        if (ext_dl := self.external_downloader) is not None:
            options.update(ext_dl._export())
        return await self.ytdownloader(url, options)

    async def audio_downloader(
        self, url: str, uid: str, rnd_key: str, prog_func: Callable
    ) -> Union[int, str]:
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
            "quiet": self.silent,
            "logtostderr": self.silent,
        }
        if (ext_dl := self.external_downloader) is not None:
            options.update(ext_dl._export())
        return await self.ytdownloader(url, options)

    @run_sync
    def ytdownloader(self, url: str, options: Dict[str, Any]) -> Union[int, str]:
        try:
            with youtube_dl.YoutubeDL(options) as ytdl:
                return ytdl.download([url])
        except DownloadError:
            logger.error("[DownloadError] : Failed to Download Video")
        except GeoRestrictedError:
            logger.error(
                "[GeoRestrictedError] : The uploader has not made this video"
                " available in your country"
            )
        except Exception:
            logger.exception("Something Went Wrong")

    async def download(
        self,
        url: str,
        uid: str,
        downtype: str,
        update: Union[Message, CallbackQuery],
        with_progress: bool = True,
        edit_rate: int = 8,
    ) -> str:
        """Download Media with progress bar

        Parameters:
        ----------
            - url (`str`): Youtube_dl supported URL.
            - uid (`str`): Preferred media choice.
            - downtype (`str`): [`'audio'` | `'video'`].
            - update (`Union[Message, CallbackQuery]`): A Pyrogram update to display progress.
            - with_progress (`bool`, optional): Enable / Disable progress. (Defaults to `True`)
            - edit_rate (`int`, optional): Progress edit rate in seconds. (Defaults to `8`)

        Returns:
        -------
            `str`: Key to upload media, After successful download

        Raises:
        ------
            `TypeError`: On unsupported `downtype`
            `StopTransmission`: When download is cancelled
            `DownloadError`: In case youtube_dl download return code is not equal to 0
        """
        last_update_time = None

        process = Process(update)
        key = rnd_key()

        def prog_func(prog_data: Dict) -> None:
            nonlocal last_update_time
            now = int(time.time())
            # Only edit message once every 8 seconds to avoid ratelimits

            if process.is_cancelled:
                logger.warning("Download process is Cancelled")
                raise StopTransmission

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
                self.loop.create_task(self.progress_func(process, progress))
            last_update_time = now

        if downtype == "video":
            out = await self.video_downloader(url, uid, key, prog_func)
        elif downtype == "audio":
            out = await self.audio_downloader(url, uid, key, prog_func)
        else:
            raise TypeError(f"'{downtype}' is Unsupported !")

        if isinstance(out, int) and out == 0:
            return key
        raise DownloadError(str(out))

    @staticmethod
    async def progress_func(process: Process, text: str) -> None:
        try:
            await process.edit(
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True,
                reply_markup=process.cancel_markup,
            )
        except FloodWait as f:
            await asyncio.sleep(f.x + 2)
        except (StopPropagation, StopTransmission) as p_e:
            raise p_e
        except (ContinuePropagation, MessageNotModified):
            pass
        except Exception:
            logger.exception("Progress")
