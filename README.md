# Music Downloader

Telegram bot that downloads music  to your server/pc and automaticaly update navidrome library after downloading

Just send link to track/album/playlist/artist to bot and wait!

## Features
- Download single track with metadata
- Albums
- Playlist with .m3u8 generation
- All artist tracks
- Download in folder library with architecture **"Artist/Album (year)/num. Title.mp3"**
- Supported platforms:
  - [Yandex.Music](https://music.yandex.ru/) via [yandex-music-api](https://github.com/MarshalX/yandex-music-api)
  - [Spotify](https://open.spotify.com/) via [spotDL](https://github.com/spotDL/spotify-downloader)

## Installation guide

### Docker
1. Clone repo
```shell
git clone https://github.com/ninnjah/music-downloader-bot
cd music-downloader-bot
docker compose build
```
2. Copy and edit config file
```shell
cp config.yaml.example config.yaml
nano config.yaml
```
Config example
```yaml
# Whitelist
admin_list:
 - 1234567890
bot_token: <bot_token>
# Path for music downloading (pass if use docker)
music_path: ./music

redis:
 enabled: true
 prefix: musicbot
 host: redis  # pass if use docker
 port: 6379
 db: 0
 password:

# Don't tested yet
webhook:
 enabled: false
 url: https://localhost
 path: /tg_api/webhook
 port: 8881

yandex:
 token: <yandex_token>

spotify:
 id: <spotify_app_id>
 secret: <spotify_app_secret>

subsonic:
 username: <subsonic_login>
 password: <subsonic_password>
 salt: salty_
```
- You can get Yandex music token [here](https://yandex-music.readthedocs.io/en/main/token.html)
- Spotify id and secret [here](https://developer.spotify.com/documentation/web-api/concepts/apps)
- Subsonic data needs for automatic update library after download

**Run**
```shell
docker-compose up -d
```

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. 
Any contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. 
You can also simply open an issue with the tag "enhancement". Don't forget to give the project a star! Thanks again!

    Fork the Project
    Create your Feature Branch (git checkout -b feature/AmazingFeature)
    Commit your Changes (git commit -m 'Add some AmazingFeature')
    Push to the Branch (git push origin feature/AmazingFeature)
    Open a Pull Request

## License

The project is under the GPL-3.0 licence
