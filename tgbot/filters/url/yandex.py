from collections import defaultdict
from typing import Dict, Union, Literal

from aiogram.types import Message

from .utils.abc import UrlFilterProtocol
from .utils.types import Album, Artist, Track, Playlist, UrlList


class YandexUrlFilter(UrlFilterProtocol):
    URL_PREFIX = "https://music.yandex.ru/"

    async def __call__(self, message: Message) -> Union[bool, Dict[Literal["urls"], UrlList]]:
        if not (urls := await self.extract_urls(message)):
            return False

        parsed_urls = defaultdict(list)
        for url in urls:
            if self.URL_PREFIX not in url:
                continue

            raw_data = url.split(self.URL_PREFIX)[-1].split("?")[0].split("/")

            if raw_data[0] == "users" and len(raw_data) == 4:
                parsed_urls["playlist"].append(Playlist(url=url, id=raw_data[3], owner=raw_data[1]))
            elif raw_data[0] == "album" and len(raw_data) == 2:
                parsed_urls["album"].append(Album(url=url, id=raw_data[1]))
            elif raw_data[0] == "album" and len(raw_data) == 4:
                parsed_urls["track"].append(Track(url=url, id=raw_data[3]))
            elif raw_data[0] == "artist" and len(raw_data) == 2:
                parsed_urls["artist"].append(Artist(url=url, id=raw_data[1]))

        if len(parsed_urls) > 0:
            return {
                "urls": UrlList(
                    album=parsed_urls["album"],
                    artist=parsed_urls["artist"],
                    playlist=parsed_urls["playlist"],
                    track=parsed_urls["track"],
                )
            }
        else:
            return False
