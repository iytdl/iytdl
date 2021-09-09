__all__ = [
    "run_sync",
    "sublists",
    "humanbytes",
    "time_formater",
    "rnd_key",
    "run_command",
]

import asyncio
import logging
import os
import tempfile

from datetime import timedelta
from functools import partial, wraps
from io import BytesIO
from random import sample
from typing import Any, Awaitable, Callable, List, Optional, Tuple, Union

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
    """Format Time to Human readable format

    Parameters:
    ----------
        - value (`Union[timedelta, int]`): Pass either a `~time.timedelta` or an `int`.
        - precision (`int`, optional): Decimal Precision. (Defaults to `0`)

    Returns:
    -------
        `str`
    """
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
    """Upload Images to Telegra.ph via URL

    Parameters:
    ----------
        - http (`ClientSession`): `~aiohttp.ClientSession`.
        - url (`str`): Http Url.

    Returns:
    -------
        `Optional[str]`: Telegra.ph link on success
    """
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


async def run_command(
    *args: Any, shell: bool = False, silent: bool = False
) -> Tuple[Union[str, int]]:
    """Run Command in Shell

    Parameters:
    ----------
        - shell (`bool`, optional): For single commands. (Defaults to `False`)
        - silent (`bool`, optional): Disable error logging. (Defaults to `False`)

    Returns:
    -------
        `Tuple[Union[str, int]]`: (stdout, return code)
    """
    try:
        if shell:
            proc = await asyncio.create_subprocess_shell(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        std_out, std_err = await proc.communicate()
        if std_err and not silent:
            logger.error(std_err.decode("utf-8", "replace").strip())
    except Exception:
        if not silent:
            logger.exception(f"Failed to run command => {''.join(args)}")
        return_code = 1
        out = ""
    else:
        return_code = proc.returncode
        out = std_out.decode("utf-8", "replace").strip()
    return (out, return_code)
