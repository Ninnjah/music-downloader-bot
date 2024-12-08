import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import music_tag
import httpx
from mutagen.mp3 import MP3

from yandex_music import Album, Artist, Client, Track, Playlist
from yandex_music.exceptions import YandexMusicError, NotFoundError

from m3u8 import PlaylistGenerator
from broker_app import app
from broker.services.notification import NotificationTask
from broker.services.retry import retry
from tgbot.config_reader import config


logger = logging.getLogger(__name__)
client = Client(token=config.yandex.token)
client.init()
MUSIC_PATH = config.music.download_path
PLAYLIST_PATH = config.music.playlist_path
FORBIDDEN_SYMBOLS = r"#<$+%>!`&*‘|?{}“=>/:\@"


class YandexNote(NotificationTask):
    ENDPOINT = "note_yandex"


def _make_album_dir(album: Album) -> Tuple[Path, Path]:
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


@retry(attempt_count=5)
def _download_track(track: Track) -> Path:
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
        f"{info['track_position']} - "
        f"{''.join([_ for _ in info['title'][:80] if _ not in FORBIDDEN_SYMBOLS])}.mp3"
    )
    if os.path.exists(track_file):
        logger.info("Track already exists. Continue.")
        return track_file

    client.request.download(url=track_info["direct_link"], filename=track_file)
    logger.info("Track downloaded. Start write tag's.")

    # начинаем закачивать тэги в трек
    mp3 = music_tag.load_file(track_file)
    mp3["tracktitle"] = info["title"]
    if album["version"] is not None:
        mp3["album"] = info["album"] + " " + album["version"]
    else:
        mp3["album"] = info["album"]
    mp3["discnumber"] = info["volume_number"]
    mp3["totaldiscs"] = info["total_volumes"]
    mp3["tracknumber"] = info["track_position"]
    mp3["totaltracks"] = info["total_track"]
    mp3["genre"] = info["genre"]
    mp3["Year"] = info["album_year"]
    if track.version is not None:
        mp3["comment"] = f"{track.version} / Release date {info['album_year']}"
    else:
        mp3["comment"] = f"Release date {info['album_year']}"
    mp3["artist"] = info["artist"]
    mp3["album_artist"] = info["album_artist"]
    try:
        lyrics = client.tracks_lyrics(
            track_id=track.track_id, format="TEXT"
        ).fetch_lyrics()
    except NotFoundError:
        pass
    except Exception as e:
        logger.error(e, exc_info=True)
    else:
        with open(track_file.with_suffix(".txt"), "w") as text_song:
            text_song.write(lyrics)
        mp3["lyrics"] = lyrics

    with open(album_cover_pic, "rb") as img_in:
        mp3["artwork"] = img_in.read()
    mp3.save()
    logger.info("Tag's is wrote")

    return track_file


@app.task()
def get_album_info(album_id: Union[str, int]) -> Optional[dict]:
    try:
        album = client.albums_with_tracks(album_id)
    except YandexMusicError as e:
        logger.warning("No results found for album_id=%s - %s", album_id, e, exc_info=True)
        return
    else:
        return album.to_dict()


@app.task(base=YandexNote)
def download_album(user_id: int, album_id: Union[str, int]) -> Optional[dict]:
    if not (album := get_album_info(album_id)):
        return
    else:
        album = Album.de_json(album, client)

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

    retval = album.to_dict()
    retval.update(type="album")
    return retval


@app.task()
def get_artist_info(artist_id) -> Optional[dict]:
    try:
        artist = client.artists(artist_id)[0]
    except YandexMusicError as e:
        logger.warning("No results found for artist_id=%s - %s", artist_id, e, exc_info=True)
        return
    else:
        return artist.to_dict()


@app.task(base=YandexNote)
def download_artist(user_id: int, artist_id: Union[str, int]) -> Optional[dict]:
    if not (artist := get_artist_info(artist_id)):
        return
    else:
        artist = Artist.de_json(artist, client)

    logger.info(
        "Start download: Artist ID: %s / Artist name: %s / Direct albums: %s",
        artist.id,
        artist.name,
        artist.counts.direct_albums,
    )

    direct_albums = client.artists_direct_albums(artist_id=artist_id, page_size=1000)
    for album in direct_albums:
        download_album(album["id"])

    retval = artist.to_dict()
    retval.update(type="artist")
    return retval


@app.task()
def get_playlist_info(owner_id: str, playlist_id: int) -> Optional[dict]:
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
        return playlist.to_dict()


@app.task(base=YandexNote)
def download_playlist(user_id: int, owner_id: str, playlist_id: int) -> Optional[dict]:
    if not (playlist := get_playlist_info(owner_id, playlist_id)):
        return
    else:
        playlist = Playlist.de_json(playlist, client)

    playlist_entries = []
    old_root = Path(MUSIC_PATH)
    new_root = Path(PLAYLIST_PATH)

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
            if config.music.replace_playlist_path:
                track_path = new_root / track_path.relative_to(old_root)

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

    retval = playlist.to_dict()
    retval.update(type="playlist")
    return retval


@app.task()
def get_track_info(track_id) -> Optional[dict]:
    try:
        track = client.tracks(track_id)[0]
    except YandexMusicError as e:
        logger.warning("No results found for track_id=%s - %s", track_id, e, exc_info=True)
        return
    else:
        return track.to_dict()


@app.task(base=YandexNote)
def download_track(user_id: int, track_id: Union[str, int]) -> Optional[dict]:
    if not (track := get_track_info(track_id)):
        return
    else:
        track = Track.de_json(track, client)

    logger.info(
        "Start download: Track ID: %s / Artist name: %s / From Album: %s",
        track.id,
        track.artists_name()[0],
        track.albums[0].title,
    )

    _download_track(track)

    retval = track.to_dict()
    retval.update(type="track")
    return retval
