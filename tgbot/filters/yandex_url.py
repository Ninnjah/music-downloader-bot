from dataclasses import dataclass, fields
from collections import defaultdict, namedtuple
from typing import Dict, Union, Sequence

from aiogram.types import Message

from .text import UrlFilter

Playlist = namedtuple("Playlist", "id owner")
Album = namedtuple("Album", "id")
Artist = namedtuple("Artist", "id")
Track = namedtuple("Track", "id")


@dataclass
class UrlList:
    album: Sequence[Album] = ()
    artist: Sequence[Artist] = ()
    playlist: Sequence[Playlist] = ()
    track: Sequence[Track] = ()


class YandexUrlFilter(UrlFilter):
    URL_PREFIX = "https://music.yandex.ru/"

    async def __call__(self, message: Message) -> Union[bool, Dict[str, UrlList]]:
        if not (urls := await super().__call__(message)):
            return False

        yandex_urls = defaultdict(list)
        for url in urls["urls"]:
            if YandexUrlFilter.URL_PREFIX not in url:
                continue

            raw_data = url.split(YandexUrlFilter.URL_PREFIX)[-1].split("/")

            if raw_data[0] == "users" and len(raw_data) == 4:
                yandex_urls["playlist"].append(Playlist(id=raw_data[3], owner=raw_data[1]))
            elif raw_data[0] == "album" and len(raw_data) == 2:
                yandex_urls["album"].append(Album(id=raw_data[1]))
            elif raw_data[0] == "album" and len(raw_data) == 4:
                yandex_urls["track"].append(Track(id=raw_data[3]))
            elif raw_data[0] == "artist" and len(raw_data) == 2:
                yandex_urls["artist"].append(Artist(id=raw_data[1]))

        if len(yandex_urls) > 0:
            return {
                "urls": UrlList(
                    album=yandex_urls["album"],
                    artist=yandex_urls["artist"],
                    playlist=yandex_urls["playlist"],
                    track=yandex_urls["track"],
                )
            }
        else:
            return False

