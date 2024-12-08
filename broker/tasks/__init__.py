from . import yandex_music
from . import spotify_music

__all__ = (
    yandex_music.get_album_info, yandex_music.download_album,
    yandex_music.get_artist_info, yandex_music.download_artist,
    yandex_music.get_playlist_info, yandex_music.download_playlist,
    spotify_music.download_album,
    spotify_music.download_artist,
    spotify_music.download_playlist,
)
