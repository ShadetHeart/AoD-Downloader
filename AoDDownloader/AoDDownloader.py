#!/usr/bin/env python3

import json
import os
import re
import tempfile

import click
import ffmpeg
import requests
from bs4 import BeautifulSoup
from progress.bar import ChargingBar


class AoDDownloaderException(Exception):
    def __init__(self, message):
        super().__init__(message)


class AoDDownloader(object):
    sign_in_path = "/users/sign_in"
    base_url = "https://anime-on-demand.de"
    current_playlist: list = None
    current_token: str = None
    signed_in: bool = False

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

    def __init__(self, username: str, password: str, dub_only: bool = True):
        self.session = requests.Session()
        if username and password:
            self._sign_in(username, password)
        self.dubOnly = dub_only

    def _validate_response(self, response: requests.Response, return_obj: str = None):
        if response.status_code == 200:
            if return_obj:
                if type(return_obj) == str and return_obj == "soup":
                    soup_return = BeautifulSoup(
                        response.text, features="html.parser")
                    self.current_token = soup_return.find(
                        'input', {'name': 'authenticity_token'})['value']
                    self._set_header(response.url)
                    return soup_return
                elif type(return_obj) == str and return_obj == "json":
                    return json.loads(response.text)
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

    def _sign_in(self, username: str, password: str):
        self._validate_response(
            self.session.get(self.sign_in_url), return_obj='soup')
        self._validate_response(
            self.session.post(
                self.sign_in_url,
                data={"utf8": "&#x2713;", "user[login]": username,
                      "user[password]": password,
                      "user[remember_me]": "0", "authenticity_token": self.token}))
        self.signed_in = True

    def _parse_episode(self, episode_data: dict) -> Episode:
        episode_url = episode_data['sources'][0]['file']
        episode_base_url = episode_url.split('index.m3u8')[0] + '/'

        episode_title = (episode_data['title'] + episode_data['description']
                         ).replace(" - ", "_").replace(" ", "_").replace(",", "")

        # TODO: support streamlock!
        # streamlock or cloudfround differentiation
        # if("streamlock" in episode_url):
        #     while(quality_counter < quality_option):
        #         episode_chunklist_url = episode_chunklist_url[(
        #             episode_chunklist_url.find("RESOLUTION")+10):]
        #         quality_counter = quality_counter + 1
        #     episode_chunklist_url = episode_chunklist_url[(episode_chunklist_url.find(
        #         "chunklist")):(episode_chunklist_url.find('.m3u8')+5)]
        #     episode_chunklist_url = episode_url[:(
        #         episode_url.find(".smil")+6)] + episode_chunklist_url
        # else:
        #     while(quality_counter < quality_option):
        #         episode_chunklist_url = episode_chunklist_url[(
        #             episode_chunklist_url.find("RESOLUTION")+10):]
        #         quality_counter = quality_counter + 1
        #     episode_chunklist_url = episode_chunklist_url[(episode_chunklist_url.find(
        #         "CODECS=")+31):(episode_chunklist_url.find("Id=")+23)]
        #     episode_chunklist_url = episode_url[:(
        #         episode_url.find('index.m3u8'))]+"/" + episode_chunklist_url

        episode_chunk_list_url = episode_base_url + self._validate_response(
            self.session.get(episode_url), return_obj="m3u")[0]  # For now only use best quality

        raw_chunk_list = self._validate_response(
            self.session.get(episode_chunk_list_url), return_obj="m3u")

        # TODO: support streamlock!
        # clean chunklist
        # if("streamlock" in episode_url):
        #     chunks = re.findall("media.*", episode_chunklist)
        #     episode_chunklist = ""
        #     for line in chunks:
        #         episode_chunklist = episode_chunklist + \
        #             (episode_url[:(episode_url.find(".smil")+6)] + line) + "\n"
        #
        # else:
        #     chunks = re.findall("..\/..\/..\/.*", episode_chunklist)
        #     episode_chunklist = ""
        #     for line in chunks:
        #         episode_chunklist = episode_chunklist + \
        #             (episode_url[:(episode_url.find('index.m3u8'))
        #                         ] + line[8:]) + "\n"
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

    def set_playlist(self, anime_url):
        if not self.signed_in:
            click.echo("No user logged in. Use login command.")
            exit(1)
        if re.match("https://(www\.)?anime-on-demand\.de/anime/\d+", anime_url) is None:
            raise AoDDownloaderException(
                "Given url does not match a playlist url")
        response = self._validate_response(
            self.session.get(anime_url), return_obj='soup')
        stream = response.find('input', {'title': 'Deutschen Stream starten'}) if self.dubOnly else response.find(
            'input', {'title': 'Japanischen Stream mit Untertiteln starten'})
        if not stream or not stream['data-playlist']:
            raise AoDDownloaderException("Could not determine {lang} stream for {url}".format(
                lang="german" if self.dubOnly else "japanese", url=anime_url))
        playlist_url = f"https://www.anime-on-demand.de{stream['data-playlist']}"
        playlist_data = self._validate_response(
            self.session.get(playlist_url), return_obj='json').get('playlist')

        self.current_playlist = [self._parse_episode(
            episodeData) for episodeData in playlist_data]

    def download(self):
        if not os.path.exists('downloads'):
            os.mkdir('downloads')
        for episode in self.playlist:
            if episode.exists:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                episode_chunks = []
                bar = ChargingBar(f"{episode.title}:",
                                  max=len(episode.chunkList))
                for chunkName, chunkUrl in episode.chunkList:
                    chunk_file_name = f"{tmp}/{chunkName}"
                    with open(chunk_file_name, 'wb') as chunk:
                        chunk_response = self.session.get(chunkUrl)
                        if chunk_response.status_code != 200:
                            raise AoDDownloaderException("Download failed")
                        chunk.write(chunk_response.content)
                    ffmpeg_input = ffmpeg.input(chunk_file_name)
                    episode_chunks.append(ffmpeg_input.video)
                    episode_chunks.append(ffmpeg_input.audio)
                    bar.next()
                bar.finish()
                click.echo(f"Converting {episode.title}... ")
                ffmpeg.concat(*episode_chunks, v=1,
                              a=1).output(episode.file).run(capture_stderr=True)
                click.echo("Finished")
