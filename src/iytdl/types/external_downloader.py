__all__ = ["ExternalDownloader", "Aria2c"]

from dataclasses import dataclass
from typing import Dict, List, Union


class ExternalDownloader:
    def _export(self) -> Dict[str, Union[str, List[str]]]:
        attrs = list(self.__dataclass_fields__)
        if "executable_path" in attrs:
            ext_dl = self.executable_path
            attrs.remove("executable_path")
        else:
            ext_dl = self.__class__.__name__.lower()

        return dict(
            external_downloader=ext_dl,
            external_downloader_args=list(
                map(
                    lambda x: f"--{x.replace('_', '-')}={getattr(self, x)}",
                    attrs,
                )
            ),
        )


@dataclass
class Aria2c(ExternalDownloader):
    """Aria2c External Downloader"""

    executable_path: str = "aria2c"
    max_concurrent_downloads: int = 5
    max_connection_per_server: int = 1
    split: int = 5
    min_split_size: str = "20M"
