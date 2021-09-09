import asyncio
import sys

from iytdl import iYTDL


LOG_GROUP_ID = ""


async def test_iytdl_download():
    async with iYTDL(
        log_group_id=LOG_GROUP_ID,
        cache_path="downloads",
    ) as ytdl:

        def prog_func(*_, **__):
            pass

        status_code = await ytdl.video_downloader(
            "https://www.dailymotion.com/embed/video/kVUUPJE2HHun2qxaTxN",
            "bestvideo+bestaudio/best",
            "folder_59r5vewes",
            prog_func,
        )
        if isinstance(status_code, int) and status_code == 0:
            print("Download Successfull")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(test_iytdl_download())
