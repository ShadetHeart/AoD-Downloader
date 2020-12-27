#!/usr/bin/env python3

import json
import os
import re
import tempfile

import click
import ffmpeg
import requests
from bs4 import BeautifulSoup

from .config import Config
from .quality import Quality


class AoDDownloaderException(Exception):
    def __init__(self, message):
        super().__init__(message)


class AoDDownloader(object):
    sign_in_path = "/users/sign_in"
    base_url = "https://anime-on-demand.de"
    current_playlist: list = None
    current_token: str = None
    signed_in: bool = False
    prompted_quality: bool = False

    class Episode(object):
        def __init__(self, title: str, chunk_list: list):
            self.title = title
            self.chunkList = chunk_list

        def __str__(self):
            return f"Episode({self.title}, {len(self.chunkList)} chunks)"

        def __repr__(self):
            return self.__str__()

        @property
        def exists(self) -> bool:
            return os.path.exists(self.file)

        @property
        def file(self) -> str:
            return f"{self.title}.mkv"

    def __init__(self, config: Config):
        self.session = requests.Session()
        self.config = config
        if self.config.username and self.config.password:
            self._sign_in()

    def _validate_response(self, response: requests.Response, return_obj: str = None):
        if response.status_code == 200:
            if return_obj:
                if type(return_obj) == str and return_obj == "soup":
                    soup_return = BeautifulSoup(
                        response.text, features="html.parser")
                    self.current_token = soup_return.find(
                        'meta', {'name': 'csrf-token'})['content']
                    self._set_header(response.url)
                    return soup_return
                elif type(return_obj) == str and return_obj == "json":
                    return response.json()
                elif type(return_obj) == str and return_obj == "raw":
                    return response.text
                elif type(return_obj) == str and return_obj == "m3u":
                    m3u_result = []
                    for line in response.text.split("\n"):
                        if not line.startswith('#'):
                            if line.strip():
                                m3u_result.append(line.strip())
                    if not m3u_result:
                        raise AoDDownloaderException("No m3u Content found")
                    return m3u_result
                else:
                    raise AoDDownloaderException(
                        f"{return_obj} is not supported. Valid values are: soup, json, raw, m3u")
            else:
                return
        reason = ''
        try:
            content = json.loads(response.text)
            if content.get('error') is not None:
                reason = f"Error: {content.get('error')}"
        except:
            pass
        raise AoDDownloaderException(
            f"Request returned {response.status_code}. {reason}")

    def _sign_in(self):
        self._validate_response(
            self.session.get(self.sign_in_url), return_obj='soup')
        self._validate_response(
            self.session.post(
                self.sign_in_url,
                data={"utf8": "&#x2713;", "user[login]": self.config.username,
                      "user[password]": self.config.password,
                      "user[remember_me]": "0", "authenticity_token": self.token}))
        self.signed_in = True

    def _parse_episode(self, episode_data: dict) -> Episode:
        episode_url = episode_data['sources'][0]['file']
        episode_base_url = episode_url.split('index.m3u8')[0] + '/'

        episode_title = (" ".join([episode_data['title'], episode_data['description']])
                         ).replace(" - ", "_").replace(" ", "_").replace(",", "")

        episode_chunk_list_url_array = [episode_base_url + url_path for url_path in self._validate_response(
            self.session.get(episode_url), return_obj="m3u")]

        if not self.config.quality:
            self.config.setQuality()

        selected_quality = self.config.quality.value
        if abs(selected_quality) > len(episode_chunk_list_url_array):
            selected_quality = -1 * len(episode_chunk_list_url_array)
            if not self.prompted_quality:
                click.echo(f"Max quality is not available. {Quality(selected_quality).name.upper()} will be used.")
                self.prompted_quality = True

        episode_chunk_list_url = episode_chunk_list_url_array[selected_quality]
        raw_chunk_list = self._validate_response(
            self.session.get(episode_chunk_list_url), return_obj="m3u")

        chunk_list = [(chunk.split('?')[0].split('/')[-1], chunk.replace("../../../", episode_base_url))
                      for chunk in raw_chunk_list]
        return self.Episode(episode_title, chunk_list)

    def _set_header(self, url: str):
        self.session.headers.update({"X-CSRF-Token": self.token, "Accept-Encoding": "gzip, deflate, br",
                                     "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                                     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
                                     "Accept": "application/json, text/javascript, */*; q=0.01", "Referer": url,
                                     "X-Requested-With": "XMLHttpRequest", "Connection": "keep-alive"})

    @property
    def sign_in_url(self) -> str:
        return self.base_url + self.sign_in_path

    @property
    def playlist(self) -> list:
        return self.current_playlist

    @property
    def token(self) -> str:
        return self.current_token

    def set_playlist(self, anime_url: str, verbose: bool):
        if not self.signed_in:
            click.echo("No user logged in. Use login command.")
            exit(1)
        if re.match("https://(www\.)?anime-on-demand\.de/anime/\d+", anime_url) is None:
            raise AoDDownloaderException(
                "Given url does not match a playlist url")
        if verbose:
            click.echo("Matched playlist url")

        if not self.config.german and not self.config.japanese:
            if verbose:
                click.echo("No language selection found")
            japanese, german = self.config.setLanguages()
            if not german and not japanese:
                raise AoDDownloaderException("No language chosen. Please choose at least one.")
        else:
            german = self.config.german
            japanese = self.config.japanese

        response = self._validate_response(
            self.session.get(anime_url), return_obj='soup')
        streams = {}
        if german:
            if verbose:
                click.echo("Set german stream")
            streams["german"] = response.find('input', {'title': 'Deutschen Stream starten'})
        if japanese:
            if verbose:
                click.echo("Set japanese stream")
            streams["japanese"] = response.find('input', {'title': 'Japanischen Stream mit Untertiteln starten'})

        if (not streams.get("german") or not streams.get("german")['data-playlist']) and (
                not streams.get("japanese") or not streams.get("japanese")['data-playlist']):
            raise AoDDownloaderException(
                f"Could not determine stream for {anime_url}. Selected language may not be available")

        playlist_data = []
        for stream in streams:
            playlist_url = f"https://www.anime-on-demand.de{streams[stream]['data-playlist']}"
            for episode in self._validate_response(
                    self.session.get(playlist_url), return_obj='json').get('playlist'):
                if len(stream) > 1:
                    episode['description'] += f"_{stream[:3].upper()}"
                playlist_data.append(episode)

        self.current_playlist = [self._parse_episode(
            episodeData) for episodeData in playlist_data]

    def download(self, verbose: bool):
        for episode in self.playlist:
            if episode.exists:
                click.echo(f"{click.style(f'Skipping {episode.title}.', fg='green')} Already exists.")
                continue
            with tempfile.TemporaryDirectory() as tmp:
                episode_chunks = []
                with click.progressbar(episode.chunkList, label=f"Downloading {episode.title}:") as chunkList:
                    for chunkName, chunkUrl in chunkList:
                        chunk_file_name = f"{tmp}/{chunkName}"
                        with open(chunk_file_name, 'wb') as chunk:
                            chunk_response = self.session.get(chunkUrl)
                            if chunk_response.status_code != 200:
                                # Retry download of chunk once.
                                chunk_response = self.session.get(chunkUrl)
                                if chunk_response.status_code != 200:
                                    raise AoDDownloaderException(f"Download failed with status code {chunk_response.status_code}")
                            chunk.write(chunk_response.content)
                        ffmpeg_input = ffmpeg.input(chunk_file_name)
                        episode_chunks.append(ffmpeg_input.video)
                        episode_chunks.append(ffmpeg_input.audio)
                click.echo(f"Converting {episode.title}... ")
                try:
                    ffmpeg.concat(*episode_chunks, v=1,
                                  a=1).output(episode.file).run(capture_stderr=not verbose)
                except FileNotFoundError:
                    raise AoDDownloaderException("ffmpeg is not installed. Please install ffmpeg")
                click.echo(click.style(f"Finished {episode.title}", fg='green'))
