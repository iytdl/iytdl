<center><img src="https://i.imgur.com/h7i3L6g.png"></center>

# iYTDL

<p align="center">
<a href="https://github.com/iytdl/iytdl/actions"><img alt="Actions Status" src="https://github.com/psf/black/workflows/Test/badge.svg"></a>
<a href="https://github.com/psf/black/actions"><img alt="Actions Status" src="https://github.com/psf/black/workflows/Primer/badge.svg"></a>
<a href="https://github.com/iytdl/iytdl/blob/main/LICENSE"><img alt="License: GPLv3" src="https://img.shields.io/badge/License-GPLv3-blue.svg"></a>
<a href="https://pypi.org/project/iytdl/"><img alt="PyPI" src="https://img.shields.io/pypi/v/iytdl"></a>
<a href="https://pepy.tech/project/iytdl"><img alt="Downloads" src="https://pepy.tech/badge/iytdl"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

<h2 align="center">Async Standalone Inline YouTube-DL Module</h2>

## ⭐️ Features

- Fully Asynchronous
- Fast and Memory Efficient (uses Aiosqlite for Caching)
- Uses search query based sha1 hashes to store results to avoid storing duplicate data
- Supports Context Manager
- [Supported Sites](https://ytdl-org.github.io/youtube-dl/supportedsites.html)

## Requirements

- Python >=3.8,<4
- A Pyrogram Based Bot
- FFmpeg

## Callbacks

- Back and Next

```python
r"^yt_(back|next)\|(?P<key>[\w-]{5,11})\|(?P<pg>\d+)$"
```

- List View

```python
r"^yt_listall\|(?P<key>[\w-]{5,11})$"
```

- Extract Info

```python
r"^yt_extract_info\|(?P<key>[\w-]{5,11})$"
```

- Download

```python
r"yt_(?P<mode>gen|dl)\|(?P<key>[\w-]+)\|(?P<choice>[\w-]+)\|(?P<dl_type>a|v)$"
```

## Usage

- Detailed usage with example

### [iytdl_example.py](https://github.com/iytdl/iytdl/blob/master/example/iytdl_example.py)
