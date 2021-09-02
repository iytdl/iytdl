import asyncio
import sys

from pyrogram import Client

from iytdl import iYTDL
from iytdl.types.external_downloader import Aria2c


API_ID = ""
API_HASH = ""
BOT_TOKEN = ""
LOG_GROUP_ID = ""

# Test for Download, Upload and Aria2c


async def test_dl_upload_aria():
    async with Client(":memory:", API_ID, API_HASH, bot_token=BOT_TOKEN) as app:
        async with iYTDL(
            log_group_id=LOG_GROUP_ID,
            external_downloader=Aria2c(executable_path=""),
            cache_path="downloads",
        ) as ytdl:
            msg = await app.send_photo(
                LOG_GROUP_ID,
                photo="https://i.imgur.com/Q94CDKC.png",
                caption="",
            )
            key = await ytdl.download(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                ytdl.get_choice_by_id("mp4", "video", yt_url=True)[0],
                with_progress=True,
                downtype="video",
                update=msg,
            )

            if key is not None:
                await ytdl.upload(app, key, "video", msg)


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
asyncio.run(test_dl_upload_aria())
