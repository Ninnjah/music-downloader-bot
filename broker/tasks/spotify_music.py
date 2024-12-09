import logging
from dataclasses import asdict
from pathlib import Path
from typing import Optional, List

import httpx
from spotdl import Spotdl
from spotdl.types.options import DownloaderOptionalOptions
from spotdl.types.song import Song
from spotipy.exceptions import SpotifyException

from m3u8 import PlaylistGenerator
from broker_app import app
from broker.services.notification import NotificationTask
from tgbot.config_reader import config


logger = logging.getLogger(__name__)
MUSIC_PATH = config.music.download_path
PLAYLIST_PATH = config.music.playlist_path
client = Spotdl(
    client_id=config.spotify.id,
    client_secret=config.spotify.secret,
    headless=True,
    downloader_settings=DownloaderOptionalOptions(
        proxy=config.spotify.proxy,
        output=f"{MUSIC_PATH}/{{artist}}/{{album}} ({{year}})/{{track-number}}. {{title}}",
        format="mp3",
        log_level=logging.getLevelName(logging.WARNING),
    ),
)


class SpotifyNote(NotificationTask):
    ENDPOINT = "note_spotify"


def _download_album_cover(song: Song, song_path: Path):
    album_folder = song_path.parent
    album_cover_pic = Path(album_folder, "cover.jpg")
    if album_folder and not album_cover_pic.exists():
        with album_cover_pic.open("wb") as f:
            res = httpx.get(song.cover_url)
            f.write(res.content)


@app.task()
def get_info(url: str) -> Optional[List[dict]]:
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


@app.task(base=SpotifyNote)
def download_album(user_id: int, album: List[dict]) -> Optional[dict]:
    album = [Song(**song) for song in album]

    logger.info(
        "Album ID: %s / Album title - %s",
        album[0].album_id,
        album[0].album_name,
    )

    track_list = client.download_songs(album)
    _download_album_cover(*track_list[0])

    retval = asdict(album[0])
    retval.update(type="album")
    return retval


@app.task(base=SpotifyNote)
def download_artist(user_id: int, artist: List[dict]) -> Optional[dict]:
    artist = [Song(**song) for song in artist]
    album_count = len(set(song.album_id for song in artist))

    logger.info(
        "Start download: Artist ID: %s / Artist name: %s / Direct albums: %s",
        artist[0].artist_id,
        artist[0].artist,
        album_count,
    )

    track_list = client.download_songs(artist)
    parsed_albums = []

    for track, track_path in track_list:
        if track.album_id not in parsed_albums:
            _download_album_cover(track, track_path)
        parsed_albums.append(track.album_id)

    retval = asdict(artist[0])
    retval.update(type="artist")
    return retval


@app.task(base=SpotifyNote)
def download_playlist(user_id: int, playlist: List[dict]) -> Optional[dict]:
    playlist = [Song(**song) for song in playlist]
    playlist_entries = []
    old_root = Path(MUSIC_PATH)
    new_root = Path(PLAYLIST_PATH)

    logger.info(
        "Playlist URL: %s / Playlist title - %s",
        playlist[0].list_url,
        playlist[0].list_name,
    )

    parsed_albums = []
    track_list = client.download_songs(playlist)
    for track, track_path in track_list:
        if track.album_id not in parsed_albums:
            _download_album_cover(track, track_path)
        parsed_albums.append(track.album_id)

        if config.music.replace_playlist_path:
            track_path = new_root / track_path.relative_to(old_root)

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


@app.task(base=SpotifyNote)
def download_track(user_id: int, song: dict) -> Optional[dict]:
    song = Song(**song)

    logger.info(
        "Start download: Track ID: %s / Artist name: %s / From Album: %s",
        song.song_id,
        song.artist,
        song.album_name,
    )

    track, track_path = client.download(song)
    _download_album_cover(track, track_path)

    retval = asdict(song)
    retval.update(type="track")
    return retval
