<p align="center">
<img src="https://i.imgur.com/Q94CDKC.png" width=250px>

# iYTDL

<a href="https://github.com/iytdl/iytdl/blob/main/LICENSE"><img alt="License: GPLv3" src="https://img.shields.io/badge/License-GPLv3-blue.svg"></a>
<a href="https://github.com/iytdl/iytdl/actions"><img alt="Actions Status" src="https://github.com/iytdl/iytdl/actions/workflows/pypi-publish.yaml/badge.svg"></a>
<a href="https://pypi.org/project/iytdl/"><img alt="PyPI" src="https://img.shields.io/pypi/v/iytdl"></a>
<a href="https://pepy.tech/project/iytdl"><img alt="Downloads" src="https://pepy.tech/badge/iytdl"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>

</p>

<h2 align="center">Async Inline YouTube-DL for Pyrogram based Bots</h2>

## ⬇️ Installation

> Install

```bash
pip3 install iytdl
```

> Upgrade

```bash
pip3 install -U iytdl
```

> Build Wheel Locally

```bash
git clone https://github.com/iytdl/iytdl.git
cd iytdl
poetry install

chmod +x scripts/install.sh && ./scripts/install.sh
```

## Features

- Async and memory efficient (uses Aiosqlite for Caching)
- Uses hashing avoid storing duplicate data
- Supports context manager
- Supports External Downloader [[Aria2c](https://github.com/iytdl/iytdl/blob/master/tests/test_download_upload.py#L20)]
- [Supported Sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Requirements

- [YT-DLP](https://github.com/yt-dlp/yt-dlp) (Active youtube-dl fork)
- [Python](https://www.python.org/) >=3.8,<4
- [Pyrogram](https://docs.pyrogram.org/) based Bot
- [FFmpeg](http://ffmpeg.org/)
- [Aria2c](https://aria2.github.io/) (_Optional_)

## Pre-commit Hooks

- [Install Pre-commit Hooks](https://pre-commit.com/#installation)
- `pre-commit install`

## Examples

### Callbacks

<details>
  <summary><b>OPEN</b></summary>

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

- Cancel

```python
r"^yt_cancel\|(?P<process_id>[\w\.]+)$"
```

</details>

### Module

### [YouTube.py](https://github.com/code-rgb/droid/blob/master/droid/modules/youtube.py)
  
## Screenshots
- **Telegram Bot:** https://t.me/iytdl_bot

> <img src="https://user-images.githubusercontent.com/88159798/136582521-ba5d0c75-5e44-4d2c-8bc7-365a1137d6a9.png" width="30%" /><img src="https://user-images.githubusercontent.com/88159798/136582483-2822123c-bb5c-47f3-8a71-5dc0fa0429ba.png" width="30%" /><img src="https://user-images.githubusercontent.com/88159798/136582503-c954c731-e0cc-444a-bd8d-9220a4e5e35c.png" width="30%" /><img src="https://user-images.githubusercontent.com/88159798/136582494-4193b4f2-9db0-4a5f-b799-deb81b7b3245.png" width="30%" /><img src="https://user-images.githubusercontent.com/88159798/136582514-bbac6cb4-0a49-4689-9da2-b30abb4de443.png" width="30%" /><img src="https://user-images.githubusercontent.com/88159798/136582506-f202cb07-3ce3-480b-8709-8d39f1f04540.png" width="30%" /><img src="https://user-images.githubusercontent.com/88159798/136582476-dac517f3-34b0-4497-96de-98031ace4a65.png" width="30%" />
