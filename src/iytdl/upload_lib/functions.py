__all__ = ["unquote_filename", "thumb_from_audio", "covert_to_jpg", "take_screen_shot"]

import re

from io import BytesIO
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import mutagen

from PIL import Image

from iytdl.upload_lib import ext
from iytdl.utils import run_command


def unquote_filename(filename: Union[Path, str]) -> str:
    """
    Removes single and double quotes from filename to avoid ffmpeg errors
    due to unclosed quotation in filename

    Parameters:
    ----------
        - filename (`Union[Path, str]`): Full file name.

    Returns:
    -------
        `str`: New filename after renaming original file

    """
    file = Path(filename) if isinstance(filename, str) else filename
    un_quoted = file.parent.joinpath(re.sub(r"[\"']", "", file.name))
    if file.name != un_quoted.name:
        file.rename(un_quoted)
        return str(un_quoted)
    return str(filename)


def thumb_from_audio(filename: Union[Path, str]) -> Optional[str]:
    """Extract album art from audio

    Parameters:
    ----------
        - filename (`Union[Path, str]`): audio file path.

    Returns:
    -------
        `Optional[str]`: if audio has album art

    """
    file = Path(filename) if isinstance(filename, str) else filename
    if not (audio_id3 := mutagen.File(str(file))):
        return
    thumb_path = file.parent.joinpath("album_art.jpg")
    for key in audio_id3.keys():
        if "APIC" in key and (album_art := getattr(audio_id3[key], "data", None)):
            thumb_path = file.parent.joinpath("album_art.jpg")
            with BytesIO(album_art) as img_io:
                with Image.open(img_io) as img:
                    img.convert("RGB").save(str(thumb_path), "JPEG")
            break
    if thumb_path.is_file():
        return str(thumb_path)


def covert_to_jpg(filename: Union[Path, str]) -> Tuple[str, Tuple[int]]:
    """Convert images to Telegram supported thumb

    Parameters:
    ----------
        - filename (`Union[Path, str]`): Image file path.

    Returns:
    -------
        `Tuple[str, Tuple[int]]`: (thumb_path, dimensions)

    """
    file = Path(filename) if isinstance(filename, str) else filename
    with Image.open(file) as img:
        if file.name.lower().endswith(ext.photo[:2]):
            thumb_path = str(file)
        else:
            thumb_path = str(file.parent.joinpath(f"{file.stem}.jpeg"))
            img.convert("RGB").save(thumb_path, "JPEG")
        size = img.size
    return thumb_path, size


async def take_screen_shot(
    video_file: str, ttl: int = -1, **kwargs: Any
) -> Optional[str]:
    """Generate Thumbnail from video

    Parameters:
    ----------
        - video_file (`str`): Video file path.
        - ttl (`int`, optional): Timestamp (default `-1` i.e use ffprobe).
        - **kwargs (`Any`, optional) Pass ffmpeg and ffprobe custom path.

    Returns:
    -------
        `Optional[str]`: On Success
    """
    file = Path(video_file)
    ss_path = file.parent.joinpath(f"{file.stem}.jpg")
    vid_path = f'"{video_file}"'
    if ttl == -1:
        try:
            get_duration = [
                kwargs.get("ffprobe", "ffprobe"),
                "-i",
                vid_path,
                "-v",
                "quiet",
                "-show_entries",
                "format=duration",
                "-hide_banner",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
            ]
            _dur, _rt_code = await run_command(" ".join(get_duration), shell=True)

            if _rt_code != 0:
                return
            ttl = int(float(_dur)) // 2
        except Exception:
            return
    cmd = [
        kwargs.get("ffmpeg", "ffmpeg"),
        "-hide_banner",
        "-loglevel error",
        "-ss",
        str(ttl),
        "-i",
        vid_path,
        "-vframes",
        "1",
        f'"{ss_path}"',
    ]
    rt_code = (await run_command(" ".join(cmd), shell=True))[1]
    if rt_code == 0 and ss_path.is_file():
        return str(ss_path)
