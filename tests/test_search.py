from iytdl import iYTDL
import pytest

LOG_GROUP_ID = 0


@pytest.mark.asyncio
async def test_search_parse():
    async with iYTDL(
        log_group_id=LOG_GROUP_ID,
        cache_path="cache",
    ) as ytdl:

        search_info = await ytdl.parse("pewdiepie minecraft")
        assert search_info
        print("Search INFO", search_info, sep="\n")

        url_info = await ytdl.parse("https://www.youtube.com/watch?v=VGt-BZ-SxGI")
        assert url_info
        print("URL INFO", url_info, sep="\n")

        extracted_info = await ytdl.parse(
            "https://www.dailymotion.com/embed/video/kVUUPJE2HHun2qxaTxN", extract=True
        )
        assert extracted_info
        print("Extracted INFO =>", extracted_info, sep="\n")
