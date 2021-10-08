import pytest

from iytdl import iYTDL


LOG_GROUP_ID = 0


@pytest.mark.asyncio
async def test_download():
    async with iYTDL(
        log_group_id=LOG_GROUP_ID,
        cache_path="cache",
    ) as ytdl:

        def prog_func(*_, **__):
            pass

        status_code = await ytdl.video_downloader(
            "https://www.dailymotion.com/embed/video/kVUUPJE2HHun2qxaTxN",
            "best",
            "folder_59r5vewes",
            prog_func,
        )
        assert isinstance(status_code, int)
        assert status_code == 0
        print("Download Successfull")
