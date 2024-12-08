from collections import defaultdict
from typing import Dict, Union, Literal

from aiogram.types import Message

from .utils.abc import UrlFilterProtocol
from .utils.types import Album, Artist, Track, Playlist, UrlList

"https://open.spotify.com/artist/2n2RSaZqBuUUukhbLlpnE6"
"https://open.spotify.com/track/0S38Oso3I9vpDXcTb7kYt9"
"https://open.spotify.com/album/1gjugH97doz3HktiEjx2vY"
"https://open.spotify.com/playlist/6yq8meYJBZaS2wRq2gFbY5"


class SpotifyUrlFilter(UrlFilterProtocol):
    URL_PREFIX = "https://open.spotify.com/"

    async def __call__(self, message: Message) -> Union[bool, Dict[Literal["urls"], UrlList]]:
        if not (urls := await self.extract_urls(message)):
            return False

        parsed_urls = defaultdict(list)
        for url in urls:
            if self.URL_PREFIX not in url:
                continue

            raw_data = url.split(self.URL_PREFIX)[-1].split("?")[0].split("/")

            if raw_data[0] == "playlist":
                parsed_urls["playlist"].append(Playlist(url=url, id=raw_data[1], owner=None))
            elif raw_data[0] == "album":
                parsed_urls["album"].append(Album(url=url, id=raw_data[1]))
            elif raw_data[0] == "artist":
                parsed_urls["artist"].append(Artist(url=url, id=raw_data[1]))
            elif raw_data[0] == "track":
                parsed_urls["track"].append(Track(url=url, id=raw_data[1]))

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
