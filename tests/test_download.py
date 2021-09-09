import asyncio

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
            "best",
            "folder_59r5vewes",
            prog_func,
        )
        if isinstance(status_code, int) and status_code == 0:
            print("Download Successfull")


asyncio.run(test_iytdl_download())
