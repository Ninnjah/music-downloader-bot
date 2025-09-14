from collections import namedtuple
from dataclasses import dataclass
from typing import Sequence

Playlist = namedtuple("Playlist", "url id")
Album = namedtuple("Album", "url id")
Artist = namedtuple("Artist", "url id")
Track = namedtuple("Track", "url id")


@dataclass
class UrlList:
    album: Sequence[Album] = ()
    artist: Sequence[Artist] = ()
    playlist: Sequence[Playlist] = ()
    track: Sequence[Track] = ()

