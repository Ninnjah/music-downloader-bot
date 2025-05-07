import logging
import os
from pathlib import Path
from typing import Optional, Tuple, Union

import httpx
from mutagen._file import File
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC, COMM, USLT
from mutagen.id3._specs import Encoding
from yandex_music import Album, Artist, Client, Playlist, Track
from yandex_music.exceptions import NotFoundError, YandexMusicError

from m3u8 import PlaylistGenerator
from tgbot.config_reader import config
from worker_app import broker

from ..middleware.notification import YandexNoteMiddleware

logger = logging.getLogger(__name__)
client = Client(token=config.yandex.token)
client.init()
MUSIC_PATH = config.music_path
FORBIDDEN_SYMBOLS = r"#<$+%>!`&*‘|?{}“=>/:\@"


def _make_album_dir(album: Album) -> Tuple[Path, Path]:
    """Create artist and album directory, download artist and album images."""

    if album.artists[0].various:
        album_folder = Path(
            MUSIC_PATH, "Various artist", f"{album.title} ({album.year})"
        )
    else:
        artist_id = album.artists[0].id
        artist_name = album.artists[0].name
        artist_folder = Path(MUSIC_PATH, artist_name)
        artist_cover_pic = Path(artist_folder, "artist.jpg")

        artist_folder.mkdir(parents=True, exist_ok=True)

        if not artist_cover_pic.exists():
            artist_info = client.artists_brief_info(artist_id=artist_id)
            artist_cover_link = artist_info.artist.cover.get_url(size="1000x1000")
            with artist_cover_pic.open("wb") as f:
                res = httpx.get(artist_cover_link)
                f.write(res.content)

        album_folder = Path(artist_folder, f"{album.title} ({album.year})")

    album_folder.mkdir(parents=True, exist_ok=True)
    album_cover_pic = Path(album_folder, "cover.jpg")
    if not album_cover_pic.exists():
        with album_cover_pic.open("wb") as f:
            res = httpx.get(album.get_cover_url("1000x1000"))
            f.write(res.content)

    return album_folder, album_cover_pic


def _download_track(track: Track) -> Path:
    """Download track with metadata."""
    album = track.albums[0]
    album_folder, album_cover_pic = _make_album_dir(album)

    track_info = client.tracks_download_info(track_id=track.track_id, get_direct_links=True)
    track_info = sorted(track_info, reverse=True, key=lambda key: key["bitrate_in_kbps"])[0]

    logger.info(
        "Start Download: ID: %s %s bitrate: %s %s",
        track.track_id,
        track.title,
        track_info["bitrate_in_kbps"],
        track_info["direct_link"],
    )

    info = {
        "title": track.title,
        "volume_number": album.track_position.volume,
        "total_volumes": len(album.volumes) if album.volumes else 1,
        "track_position": album.track_position.index,
        "total_track": album["track_count"],
        "genre": album.genre,
        "artist": track.artists_name()[0],
        "album_artist": [artist for artist in album.artists_name()],
        "album": album["title"],
    }
    if album["release_date"]:
        info["album_year"] = album["release_date"][:10]
    elif album["year"]:
        info["album_year"] = album["year"]
    else:
        info["album_year"] = ""

    track_file = (
        album_folder /
        f"{info['track_position']:02d}. "
        f"{''.join([_ for _ in info['title'][:80] if _ not in FORBIDDEN_SYMBOLS])}.mp3"
    )
    if os.path.exists(track_file):
        logger.info("Track already exists. Continue.")
    else:
        client.request.download(url=track_info["direct_link"], filename=track_file)
    logger.info("Track downloaded. Start write tag's.")

    # Add metadata to track
    encoding = track_file.suffix[1:]
    audio_file = File(str(track_file.resolve()), easy=encoding == "mp3")
    
    audio_file["artist"] = info["artist"]
    audio_file["albumartist"] = info["album_artist"]
    audio_file["title"] = info["title"]
    audio_file["date"] = info["album_year"]
    audio_file["album"] = info["album"]
    if info["genre"]:
        audio_file["genre"] = info["genre"].title()

    audio_file["tracknumber"] = f"{str(info['track_position'])}/{str(info['total_track'])}"
    audio_file["discnumber"] = str(info['volume_number'])

    audio_file.save(v2_version=3)
    audio_file = ID3(str(track_file.resolve()))
    
    try:
        lyrics = client.tracks_lyrics(
            track_id=track.track_id, format="LRC"
        ).fetch_lyrics()
    except NotFoundError:
        pass
    except Exception as e:
        logger.error(e, exc_info=True)
    else:
        with open(track_file.with_suffix(".lrc"), "w") as text_song:
            text_song.write(lyrics)

        audio_file.add(USLT(encoding=Encoding.UTF8, text=lyrics))

    with open(album_cover_pic, "rb") as img_in:
        if "APIC:Cover" in audio_file.keys():
            audio_file.pop("APIC:Cover")
        audio_file["APIC"] = APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=img_in.read(),
        )

    audio_file.save(v2_version=3)
    logger.info("Tag's is wrote")

    return track_file


@broker.task()
def get_album_info(album_id: Union[str, int], **kwargs) -> Optional[Album]:
    try:
        album = client.albums_with_tracks(album_id)
    except YandexMusicError as e:
        logger.warning("No results found for album_id=%s - %s", album_id, e, exc_info=True)
        return
    else:
        return album


@broker.task(note=YandexNoteMiddleware.LABEL)
def download_album(user_id: int, album_id: Union[str, int], **kwargs) -> Optional[Album]:
    if not (album := get_album_info(album_id)):
        return

    logger.info(
        "Album ID: %s / Album title - %s",
        album.id,
        album.title,
    )

    for n_volume, disk in enumerate(album.volumes, start=1):
        logger.info(
            "Start download: Volume №: %d из %d",
            n_volume,
            len(album.volumes),
        )

        for track in disk:
            _download_track(track)

    return album


@broker.task()
def get_artist_info(artist_id, **kwargs) -> Optional[Artist]:
    try:
        artist = client.artists(artist_id)[0]
    except YandexMusicError as e:
        logger.warning("No results found for artist_id=%s - %s", artist_id, e, exc_info=True)
        return
    else:
        return artist


@broker.task(note=YandexNoteMiddleware.LABEL)
def download_artist(user_id: int, artist_id: Union[str, int], **kwargs) -> Optional[Artist]:
    if not (artist := get_artist_info(artist_id)):
        return

    logger.info(
        "Start download: Artist ID: %s / Artist name: %s / Direct albums: %s",
        artist.id,
        artist.name,
        artist.counts.direct_albums,
    )

    direct_albums = client.artists_direct_albums(artist_id=artist_id, page_size=1000)
    for album in direct_albums:
        download_album(user_id, album["id"])

    return artist


@broker.task()
def get_playlist_info(owner_id: str, playlist_id: int, **kwargs) -> Optional[Playlist]:
    try:
        playlist = client.users_playlists(playlist_id, owner_id)
    except YandexMusicError as e:
        logger.warning(
            "No results found for owner_id=%s; playlist_id=%s - %s",
            owner_id, playlist_id, e, exc_info=True,
        )
    else:
        if isinstance(playlist, list):
            playlist = playlist[0]
        return playlist


@broker.task(note=YandexNoteMiddleware.LABEL)
def download_playlist(user_id: int, owner_id: str, playlist_id: int, **kwargs) -> Optional[Playlist]:
    if not (playlist := get_playlist_info(owner_id, playlist_id)):
        return

    playlist_entries = []

    logger.info(
        "Playlist owner: %s / Playlist ID: %s / Playlist title - %s",
        playlist.owner.login,
        playlist.playlist_id,
        playlist.title,
    )

    for track_info in playlist.tracks:
        track_path = _download_track(track_info.track)
        if track_path:
            audio = MP3(track_path)

            playlist_entries.append(
                {
                    "name": track_path.as_posix(),
                    "title": " - ".join((audio['TPE1'][0], audio['TIT2'][0])),
                    "duration": audio.info.length
                }
            )

    playlist_path = Path(MUSIC_PATH, playlist.title).with_suffix(".m3u")
    with playlist_path.open("w") as f:
        f.write(PlaylistGenerator(playlist_entries, playlist_name=playlist.title).generate())

    return playlist


@broker.task()
def get_track_info(track_id, **kwargs) -> Optional[Track]:
    try:
        track = client.tracks(track_id)[0]
    except YandexMusicError as e:
        logger.warning("No results found for track_id=%s - %s", track_id, e, exc_info=True)
        return
    else:
        return track


@broker.task(note=YandexNoteMiddleware.LABEL)
def download_track(user_id: int, track_id: Union[str, int], **kwargs) -> Optional[Track]:
    if not (track := get_track_info(track_id)):
        return

    logger.info(
        "Start download: Track ID: %s / Artist name: %s / From Album: %s",
        track.id,
        track.artists_name()[0],
        track.albums[0].title,
    )

    _download_track(track)

    return track
