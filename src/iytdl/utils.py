__all__ = [
    "run_sync",
    "sublists",
    "humanbytes",
    "time_formater",
    "take_screen_shot",
    "rnd_key",
]

import asyncio
import logging
import os
import tempfile

from datetime import timedelta
from functools import partial, wraps
from io import BytesIO
from pathlib import Path
from random import sample
from typing import Any, Awaitable, Callable, List, Optional, Union

from aiohttp import ClientSession, FormData
from PIL import Image

from iytdl.constants import *  # noqa ignore=F405


_CHAR: List[str] = list("_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxy")
logger = logging.getLogger(__name__)


def run_sync(func: Callable[..., Any]) -> Awaitable[Any]:
    """Runs the given sync function (optionally with arguments) on a separate thread."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any):
        return await asyncio.get_running_loop().run_in_executor(
            None, partial(func, *args, **kwargs)
        )

    return wrapper


def sublists(input_list: List[Any], width: int = 3) -> List[List[Any]]:
    """retuns a single list of multiple sublist of fixed width"""
    return [input_list[x : x + width] for x in range(0, len(input_list), width)]


def humanbytes(size: Union[float, int]) -> str:
    """humanize size"""
    if not size:
        return ""
    power = 1024
    t_n = 0
    power_dict = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        t_n += 1
    return "{:.2f} {}B".format(size, power_dict[t_n])


def time_formater(value: Union[timedelta, int], precision: int = 0) -> str:
    pieces = []
    if isinstance(value, int):
        value = timedelta(seconds=value)
    if value.days:
        pieces.append(f"{value.days}d")

    seconds = value.seconds

    if seconds >= 3600:
        hours = int(seconds / 3600)
        pieces.append(f"{hours}h")
        seconds -= hours * 3600

    if seconds >= 60:
        minutes = int(seconds / 60)
        pieces.append(f"{minutes}m")
        seconds -= minutes * 60

    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}s")

    if precision == 0:
        return " ".join(pieces)

    return " ".join(pieces[:precision])


def rnd_key(length: int = 8) -> str:
    return "".join(sample(_CHAR, length))


async def upload_to_telegraph(http: ClientSession, url: str) -> Optional[str]:
    async with http.get(url) as img_url:
        img_bytes = await img_url.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_img:
        f_name = temp_img.name
    with Image.open(BytesIO(img_bytes)) as img:
        img.convert("RGB").save(f_name, format="JPEG")
    data = FormData()
    data.add_field(
        name="file",
        value=open(f_name, "rb"),
        content_type="image/jpeg",
        filename="blob",
    )
    async with http.post(
        f"{TELEGRA_PH}/upload",
        headers=TELEGRA_PH_HEADERS,
        data=data,
    ) as resp:
        try:
            return f"{TELEGRA_PH}{(await resp.json())[0].get('src')}"
        except Exception:
            pass
    await run_sync(os.remove)(f_name)


async def take_screen_shot(video_file: str, ttl: int) -> Optional[str]:
    """Generate Thumbnail from video"""
    file = Path(video_file)
    ss_path = file.parent.joinpath(f"{file.stem}.jpg")
    cmd = ["ffmpeg", "-ss", str(ttl), "-i", video_file, "-vframes", "1", str(ss_path)]
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    if stderr := await process.communicate()[1]:
        logger.error(stderr.decode("utf-8", "replace").strip())
    return str(ss_path) if ss_path.is_file() else None
