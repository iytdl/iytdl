import pytest

from pyrogram import Client

from iytdl import iYTDL
from iytdl.types.external_downloader import Aria2c


API_ID = ""
API_HASH = ""
BOT_TOKEN = ""
LOG_GROUP_ID = ""

# Test for Download, Upload and Aria2c


@pytest.mark.asyncio
async def test_upload():
    async with Client(":memory:", API_ID, API_HASH, bot_token=BOT_TOKEN) as app:
        async with iYTDL(
            log_group_id=LOG_GROUP_ID,
            external_downloader=Aria2c(executable_path=""),
            cache_path="cache",
        ) as ytdl:
            msg = await app.send_photo(
                LOG_GROUP_ID,
                photo="https://i.imgur.com/Q94CDKC.png",
                caption="",
            )
            assert msg
            key = await ytdl.download(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                ytdl.get_choice_by_id("mp4", "video", yt_url=True)[0],
                with_progress=True,
                downtype="video",
                update=msg,
            )
            assert key
            assert await ytdl.upload(app, key, "video", msg)
