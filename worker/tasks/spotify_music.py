import asyncio
import logging
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional, Tuple

import httpx
from mutagen.id3 import ID3
from mutagen.id3._frames import USLT
from mutagen.id3._specs import Encoding
from spotdl import Spotdl
from spotdl.types.options import DownloaderOptionalOptions
from spotdl.types.song import Song
from spotipy.exceptions import SpotifyException

from m3u8 import PlaylistGenerator
from tgbot.config_reader import config
from worker_app import broker

from ..middleware.notification import SpotifyNoteMiddleware

logger = logging.getLogger(__name__)
MUSIC_PATH = config.music_path
NOTE_ENDPOINT = "note_spotify"
client = Spotdl(
    client_id=config.spotify.id,
    client_secret=config.spotify.secret,
    headless=True,
    downloader_settings=DownloaderOptionalOptions(
        proxy=config.spotify.proxy,
        output=f"{MUSIC_PATH}/{{artist}}/{{album}} ({{year}})/{{track-number}}. {{title}}",
        format="mp3",
        bitrate="192k",
        log_level=logging.getLevelName(logging.WARNING),
        generate_lrc=True,
    ),
)


def _download_album_cover(song: Song, song_path: Path) -> None:
    """
    Download album cover to album directory if directory exists.

    ### Arguments
    - song: The song with album cover url.
    - song_path: The path to the song
    """

    album_folder = song_path.parent
    album_cover_pic = Path(album_folder, "cover.jpg")
    if album_folder and not album_cover_pic.exists():
        with album_cover_pic.open("wb") as f:
            res = httpx.get(song.cover_url)
            f.write(res.content)


async def _download_track(song: Song) -> Tuple[Song, Optional[Path]]:
    track, track_path = client.downloader.search_and_download(song)
    lrc_path = track_path.with_suffix(".lrc")
    if lrc_path.exists():
        with lrc_path.open() as f:
            audio_file = ID3(str(track_path.resolve()))
            audio_file.add(USLT(encoding=Encoding.UTF8, text=f.read()))
            audio_file.save(v2_version=3)

    return track, track_path


@broker.task()
def get_info(url: str, **kwargs) -> Optional[List[dict]]:
    try:
        track = client.search([url])
    except SpotifyException as e:
        logger.warning("No results found for track_id=%s - %s", url, e, exc_info=True)
        return
    else:
        return [
            asdict(x)
            for x in sorted(
                track,
                key=lambda item: getattr(item, "list_position", 0) or getattr(item, "track_number", 0),
            )
        ]


@broker.task(note=SpotifyNoteMiddleware.LABEL)
async def download_album(user_id: int, album: List[dict], **kwargs) -> Optional[dict]:
    album = [Song(**song) for song in album]

    logger.info(
        "Album ID: %s / Album title - %s",
        album[0].album_id,
        album[0].album_name,
    )

    tasks = [_download_track(song) for song in album]
    track_list = await asyncio.gather(*tasks)
    _download_album_cover(*track_list[0])

    retval = asdict(album[0])
    retval.update(type="album")
    return retval


@broker.task(note=SpotifyNoteMiddleware.LABEL)
async def download_artist(user_id: int, artist: List[dict], **kwargs) -> Optional[dict]:
    artist = [Song(**song) for song in artist]
    album_count = len(set(song.album_id for song in artist))

    logger.info(
        "Start download: Artist ID: %s / Artist name: %s / Direct albums: %s",
        artist[0].artist_id,
        artist[0].artist,
        album_count,
    )

    tasks = [_download_track(song) for song in artist]
    track_list = await asyncio.gather(*tasks)
    parsed_albums = []

    for track, track_path in track_list:
        if track.album_id not in parsed_albums:
            _download_album_cover(track, track_path)
        parsed_albums.append(track.album_id)

    retval = asdict(artist[0])
    retval.update(type="artist")
    return retval


@broker.task(note=SpotifyNoteMiddleware.LABEL)
async def download_playlist(user_id: int, playlist: List[dict], **kwargs) -> Optional[dict]:
    playlist = [Song(**song) for song in playlist]
    playlist_entries = []

    logger.info(
        "Playlist URL: %s / Playlist title - %s",
        playlist[0].list_url,
        playlist[0].list_name,
    )

    parsed_albums = []
    tasks = [_download_track(song) for song in playlist]
    track_list = await asyncio.gather(*tasks)

    for track, track_path in track_list:
        if track.album_id not in parsed_albums:
            _download_album_cover(track, track_path)
        parsed_albums.append(track.album_id)

        playlist_entries.append(
            {
                "name": track_path.as_posix(),
                "title": " - ".join((track.artist, track.name)),
                "duration": track.duration,
            }
        )

    playlist_path = Path(MUSIC_PATH, playlist[0].list_name).with_suffix(".m3u")
    with playlist_path.open("w") as f:
        f.write(PlaylistGenerator(playlist_entries, playlist_name=playlist[0].list_name).generate())

    retval = asdict(playlist[0])
    retval.update(type="playlist")
    return retval


@broker.task(note=SpotifyNoteMiddleware.LABEL)
async def download_track(user_id: int, song: dict, **kwargs) -> Optional[dict]:
    song = Song(**song)

    logger.info(
        "Start download: Track ID: %s / Artist name: %s / From Album: %s",
        song.song_id,
        song.artist,
        song.album_name,
    )

    track, track_path = await _download_track(song)
    _download_album_cover(track, track_path)

    retval = asdict(song)
    retval.update(type="track")
    return retval
