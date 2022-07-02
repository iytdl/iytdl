__all__ = ["Extractor"]

import logging

from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import yt_dlp as youtube_dl

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# from youtube_dl.utils import DownloadError, ExtractorError, UnsupportedError
from yt_dlp.utils import DownloadError, ExtractorError, UnsupportedError

from iytdl.constants import YT_VID_URL
from iytdl.formatter import ResultFormatter as res_f
from iytdl.types import SearchResult
from iytdl.utils import *  # noqa ignore=F405


logger = logging.getLogger(__name__)


class Extractor:
    def __init__(self, silent: bool = False, no_warnings: bool = True) -> None:
        self.silent = silent
        self.no_warnings = no_warnings

    @run_sync
    def generic_extractor(self, key: str, url: str) -> Optional[SearchResult]:
        """Generic extractor for URLs other than YouTube
        [more info](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).

        Parameters:
        ----------
            - key (`str`): Unique key for Callback.
            - url (`str`): Http URL.

        Returns:
        -------
            `Optional[SearchResult]`: On Success
        """
        # passing key as we can't pass the entire url in callback_data
        buttons = [
            [
                InlineKeyboardButton(
                    "⭐️ BEST - 📹 Video", callback_data=f"yt_gen|{key}|mp4|v"
                ),
                InlineKeyboardButton(
                    "⭐️ BEST - 🎧 Audio", callback_data=f"yt_gen|{key}|mp3|a"
                ),
            ]
        ]
        params = {"no-playlist": True, "quiet": self.silent, "logtostderr": self.silent, "no_warnings": self.no_warnings}
        try:
            resp = youtube_dl.YoutubeDL(params).extract_info(url, download=False)
            # with open("j_debug_data.json", "w") as fx:
            #     json.dump(resp, fx, indent=4, sort_keys=True)
        except UnsupportedError:
            logger.error(f"[URL -> {url}] - is not NOT SUPPORTED")
            return
        except DownloadError as d_e:
            logger.error(f"[URL -> {url}] - {d_e}")
            return
        except ExtractorError:
            logger.warning(f"[URL -> {url}] - Failed to Extract Info")
            return SearchResult(
                key,
                "[No Information]",
                self.default_thumb,
                InlineKeyboardMarkup(buttons),
            )
        msg = f"<b><a href={url}>{resp.get('title', '[No Title]')}</a></b>\n"
        if description := resp.get("description"):
            msg += (
                f"<pre>{description[:380]}...</pre>\n"
                if len(description) > 380
                else f"<pre>{description}</pre>\n"
            )
        for info_type in ("duration", "uploader"):
            if info := resp.get(info_type):
                msg += f"{res_f.format_line(info_type.title(), info)}\n"
        if formats := (
            resp.get("formats")
            or (
                (
                    entries[0].get("formats")
                    if (entries := resp.get("entries")) and len(entries) != 0
                    else None
                )
                if resp.get("_type", "") == "playlist"
                else None
            )
        ):
            buttons += sublists(
                list(
                    map(
                        lambda x: InlineKeyboardButton(
                            " | ".join(
                                filter(
                                    None,
                                    (
                                        x.get("format"),
                                        x.get("ext"),
                                        humanbytes(v_file_size)
                                        if (v_file_size := x.get("filesize"))
                                        else None,
                                    ),
                                )
                            ),
                            callback_data=f"yt_gen|{key}|{x.get('format_id')}|v",
                        ),
                        self.filter_generic_formats(formats),
                    )
                ),
                width=1,
            )
        return SearchResult(
            key,
            msg[:1020],
            resp.get("thumbnail", self.default_thumb),
            InlineKeyboardMarkup(buttons),
        )

    def filter_generic_formats(self, raw_formats: Dict) -> Dict:
        """Filter Formats Based on 'tbr', 'width' and 'acodec'

        Parameters:
        ----------
            - raw_formats (`Dict`): Raw youtube-dl formats.

        Returns:
        -------
            `Dict`: Filtered Formats
        """
        widthset = set()

        def qual_filter(frmt) -> bool:
            if frmt.get("tbr") and frmt.get("acodec") and (width := frmt.get("width")):
                if not (width in widthset):
                    widthset.add(width)
                    return True
            return False

        frmt_list = list(
            filter(
                qual_filter,
                sorted(
                    raw_formats, key=lambda x: float(x.get("tbr") or 0), reverse=True
                ),
            )
        )[:25]
        return frmt_list if len(frmt_list) > 1 else raw_formats

    @run_sync
    def get_download_button(self, yt_id: str) -> SearchResult:
        """Generate Inline Buttons for YouTube Video

        Parameters:
        ----------
            - yt_id (`str`): YouTube video key.

        Returns:
        -------
            `SearchResult`: `~iytdl.types.SearchResult`
        """
        buttons = [
            [
                InlineKeyboardButton(
                    "⭐️ BEST - 📹 MKV", callback_data=f"yt_dl|{yt_id}|mkv|v"
                ),
                InlineKeyboardButton(
                    "⭐️ BEST - 📹 MP4",
                    callback_data=f"yt_dl|{yt_id}|mp4|v",
                ),
            ]
        ]
        best_audio_btn = [
            [
                InlineKeyboardButton(
                    "⭐️ BEST - 🎵 320Kbps - MP3",
                    callback_data=f"yt_dl|{yt_id}|mp3|a",
                )
            ]
        ]
        params = {"no-playlist": True, "quiet": self.silent, "logtostderr": self.silent, "no_warnings": self.no_warnings}
        try:
            vid_data = youtube_dl.YoutubeDL(params).extract_info(
                f"{YT_VID_URL}{yt_id}", download=False
            )
        except ExtractorError:
            vid_data = None
            buttons += best_audio_btn
        else:
            # ------------------------------------------------ #
            qual_dict = defaultdict(lambda: defaultdict(int))
            qual_list = ("1440p", "1080p", "720p", "480p", "360p", "240p", "144p")
            audio_dict: Dict[int, str] = {}
            # ------------------------------------------------ #
            for video in vid_data["formats"]:
                fr_note = video.get("format_note")
                fr_id = video.get("format_id")
                fr_size = video.get("filesize")
                if video.get("ext") == "mp4":
                    for frmt_ in qual_list:
                        if fr_note in (frmt_, frmt_ + "60"):
                            qual_dict[frmt_][fr_id] = fr_size
                if video.get("acodec") != "none":
                    bitrrate = int(video.get("abr", 0))
                    if bitrrate != 0:
                        audio_dict[
                            bitrrate
                        ] = f"🎵 {bitrrate}Kbps ({humanbytes(fr_size) or 'N/A'})"
            video_btns: List[InlineKeyboardButton] = []
            for frmt in qual_list:
                frmt_dict = qual_dict[frmt]
                if len(frmt_dict) != 0:
                    frmt_id = sorted(list(frmt_dict))[-1]
                    frmt_size = humanbytes(frmt_dict.get(frmt_id)) or "N/A"
                    video_btns.append(
                        InlineKeyboardButton(
                            f"📹 {frmt} ({frmt_size})",
                            callback_data=f"yt_dl|{yt_id}|{frmt_id}|v",
                        )
                    )
            buttons += sublists(video_btns, width=2)
            buttons += best_audio_btn
            buttons += sublists(
                list(
                    map(
                        lambda x: InlineKeyboardButton(
                            audio_dict[x], callback_data=f"yt_dl|{yt_id}|{x}|a"
                        ),
                        sorted(audio_dict.keys(), reverse=True),
                    )
                ),
                width=2,
            )

        return SearchResult(
            yt_id,
            (
                f"<a href={YT_VID_URL}{yt_id}>{vid_data.get('title')}</a>"
                if vid_data
                else ""
            ),
            vid_data.get("thumbnail") if vid_data else self.default_thumb,
            InlineKeyboardMarkup(buttons),
        )

    @staticmethod
    def get_choice_by_id(
        choice_id: str, media_type: str, yt_url: bool = True, max_filesize: int = 1950
    ) -> Tuple[str]:
        """Youtube-dl downloader formats for video / audio

        Parameters:
        ----------
            - choice_id (`str`): Format choice.
            - media_type (`str`): `"video"` or `"audio"`.
            - yt_url (`bool`, optional): If URL is from https://www.youtube.com/. (Defaults to `True`)
            - max_filesize (`int`, optional): Max video filesize (in MB).

        Returns:
        -------
            `Tuple[str]`: (Quality format, Display str)
        """
        filesize_flt = f"[filesize<?{max_filesize}M]"  # Max filesize
        if choice_id == "mkv":
            # Overall Best format
            # - can have any video format except `.webm` as it is uploaded as document.
            choice_str = f"(bestvideo+bestaudio/best)[ext!=?webm]{filesize_flt}"
            disp_str = "[ 🎵 + 📹 ]  Best"
        elif choice_id == "mp4":
            # Best streamable format i.e `.mp4`
            disp_str = "[ 🎵 + 📹 ]  Best MP4"
            if yt_url:
                choice_str = (
                    "(bestvideo[ext=mp4]+(258/256/bestaudio[ext=m4a])"
                    f"/best[ext=mp4]/best[ext!=webm]){filesize_flt}"
                )
            else:
                choice_str = (
                    "(bestvideo[ext=?mp4]+bestaudio[ext=?m4a]"
                    f"/best[ext=?mp4]/best[ext!=?webm]/best){filesize_flt}"
                )
        elif choice_id == "mp3":
            # Best audio quality upscaled to 320 kbps
            choice_str = "320"
            disp_str = "[ 🎵 ]  320 Kbps"
        else:

            if media_type == "v":
                disp_str = f"[ 🎵 + 📹 ]  {choice_id}"
                # Merge best compatible audio with choosen video quality
                if yt_url:
                    choice_str = (
                        f"({choice_id}+(258/256/bestaudio[ext=?m4a]/bestaudio)"
                        f"/best[ext=mp4]/best)[ext!=?webm]{filesize_flt}"
                    )
                else:
                    choice_str = (
                        f"({choice_id}+bestaudio/best[ext=?mp4]/best)[ext!=?webm]{filesize_flt}"
                    )
            else:
                disp_str = f"[ 🎵 ]  {choice_id}"
                # Choosen audio quality
                choice_str = choice_id
        return choice_str, disp_str
