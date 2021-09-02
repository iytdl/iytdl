__all__ = ["AioSQLiteDB"]

import os

from typing import Any, Dict, List, Optional, Tuple, Union

import aiosqlite

from iytdl.utils import rnd_key


class AioSQLiteDB:
    db: aiosqlite.Connection
    cur: aiosqlite.Cursor

    def __init__(self, db_name: str, clean: bool = False) -> None:
        """Create / Load Cache

        Parameters:
        ----------
            db_name (`str`): Cache file name.

            clean (`bool`, optional): Delete old cache and create new. (Defaults to `False`)

        """
        if clean and os.path.isfile(db_name):
            os.remove(db_name)
        self.db_name = db_name

    async def _init(self) -> None:
        """Async init"""
        try:
            self.con = await aiosqlite.connect(self.db_name)
        except aiosqlite.OperationalError:
            # DB is corrupt
            if os.path.isfile(self.db_name):
                os.remove(self.db_name)
            self.con = await aiosqlite.connect(self.db_name)
        self.cur = await self.con.cursor()
        await self.__init_tables()

    async def __init_tables(self) -> None:
        """Create required Tables"""
        await self.cur.execute(
            """
CREATE TABLE IF NOT EXISTS url_cache (
    key TEXT NOT NULL UNIQUE,
    url TEXT,
    PRIMARY KEY(key)
);"""
        )
        await self.con.commit()

    async def set_key(self, key: str, value: List[Dict[str, Any]]) -> None:
        """Set Key in Cache

        Parameters:
        ----------
            key (`str`): Unique Key.

            value (`List[Dict[str, Any]]`): YT Search Data.

        """
        await self.cur.execute(
            f"""
CREATE TABLE IF NOT EXISTS {key} (
    yt_id TEXT NOT NULL UNIQUE,
    thumb TEXT,
    title TEXT,
    body TEXT,
    duration TEXT,
    views	TEXT,
    upload_date TEXT,
    chnl_name TEXT,
    chnl_id	TEXT,
    PRIMARY KEY(yt_id)
);"""
        )
        params = list(value[0].keys())
        cmd = (
            f"INSERT INTO "
            f"{key}({', '.join(params)}) "
            f"VALUES({', '.join(['?' for _ in range(len(params))])}) "
        )
        try:
            await self.cur.executemany(
                cmd,
                [tuple(x.values()) for x in value],
            )
        except aiosqlite.IntegrityError:
            pass
        await self.con.commit()

    async def get_key(
        self, key: str, index: Optional[int] = None
    ) -> Union[Tuple[int, str, None], Dict[str, str], None]:
        """Get Data saved in Cache from Key

        Parameters:
        ----------
            key (`str`): Unique Key.

            index (`Optional[int]`, optional): Result index. (Defaults to `None`)

        Returns:
        -------
            Union[Tuple[int, str, None], Dict[str, str], None]
        """
        try:
            await self.cur.execute(f"SELECT * FROM {key}")
        except aiosqlite.OperationalError:
            return
        data = await self.cur.fetchall()
        d_len = len(data)
        if index is None:
            return data
        if 0 <= index < d_len:
            return d_len, dict(
                zip(map(lambda x: x[0], self.cur.description), data[index])
            )

    async def save_url(self, url: str) -> str:
        """Save Url and get Key.

        Parameters:
        ----------
            url (`str`): Http URL.

        Returns:
        -------
            str: Unique Key

        """
        # Check Existing Key
        await self.cur.execute("SELECT key FROM url_cache WHERE url = ?", (url,))
        if old_key := await self.cur.fetchone():
            return old_key[0]
        # New Key
        key = rnd_key(5)
        await self.cur.execute(
            "INSERT INTO url_cache(key, url) VALUES(?, ?)", (key, url)
        )
        await self.con.commit()
        return key

    async def get_url(self, key: str) -> Optional[str]:
        """Get Saved URL from Key

        Parameters:
        ----------
            key (`str`): Unique Key.

        Returns:
        -------
            Optional[str]: URL if found

        """
        await self.cur.execute("SELECT url FROM url_cache WHERE key = ?", (key,))
        if value := await self.cur.fetchone():
            return value[0]

    async def close(self) -> None:
        """Close Cache File"""
        await self.con.close()
