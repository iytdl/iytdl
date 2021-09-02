import asyncio
import sys

from iytdl import iYTDL


LOG_GROUP_ID = ""

# Test for Search


async def test_search():
    async with iYTDL(
        log_group_id=LOG_GROUP_ID,
        cache_path="downloads",
    ) as ytdl:
        search_info = await ytdl.parse("pewdiepie minecraft")
        print("Search INFO", search_info, sep="\n")
        url_info = await ytdl.parse("https://www.youtube.com/watch?v=VGt-BZ-SxGI")
        print("URL INFO", url_info, sep="\n")
        extracted_info = await ytdl.parse(
            "https://www.dailymotion.com/embed/video/kVUUPJE2HHun2qxaTxN", extract=True
        )
        print("Extracted INFO =>", extracted_info, sep="\n")


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
asyncio.run(test_search())
