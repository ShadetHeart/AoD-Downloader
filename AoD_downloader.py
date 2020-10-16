#!/usr/bin/env python3

import os
import re
import json
import ffmpeg
import asyncio
import requests
import tempfile
import configparser

from bs4 import BeautifulSoup
from progress.bar import ChargingBar


class AoDDownloaderException(Exception):
    def __init__(self, message):
        super().__init__(message)


class AoDDownloader(object):
    signInPath = "/users/sign_in"
    baseUrl = "https://anime-on-demand.de"
    currentPlaylist: list = None
    currentToken: str = None

    class Episode(object):
        def __init__(self, title: str, chunkList: list):
            self.title = title
            self.chunkList = chunkList

        def __str__(self):
            return f"Episode({self.title}, {len(self.chunkList)} chunks)"

        def __repr__(self):
            return self.__str__()

        @property
        def exists(self) -> bool:
            return os.path.exists(self.file)

        @property
        def file(self) -> str:
            return f"downloads/{self.title}.mkv"

    def __init__(self, username: str, password: str, dubOnly: bool = True):
        self.session = requests.Session()
        self._signIn(username, password)
        self.dubOnly = dubOnly

    def _validateResponse(self, response: requests.Response, returnObj: str = None):
        if response.status_code == 200:
            if returnObj:
                if type(returnObj) == str and returnObj == "soup":
                    soupReturn = BeautifulSoup(
                        response.text, features="html.parser")
                    self.currentToken = soupReturn.find(
                        'input', {'name': 'authenticity_token'})['value']
                    self._setHeader(response.url)
                    return soupReturn
                elif type(returnObj) == str and returnObj == "json":
                    return json.loads(response.text)
                elif type(returnObj) == str and returnObj == "raw":
                    return response.text
                elif type(returnObj) == str and returnObj == "m3u":
                    m3uResult = []
                    for line in response.text.split("\n"):
                        if not line.startswith('#'):
                            if line.strip():
                                m3uResult.append(line.strip())
                    if not m3uResult:
                        raise AoDDownloaderException("No m3u Content found")
                    return m3uResult
                else:
                    raise AoDDownloaderException(
                        f"{returnObj} is not supported. Valid values are: soup, json, raw, m3u")
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

    def _signIn(self, username: str, password: str):
        self._validateResponse(
            self.session.get(self.signInUrl), returnObj='soup')
        self._validateResponse(
            self.session.post(
                self.signInUrl,
                data={"utf8": "&#x2713;", "user[login]": username,
                      "user[password]": password,
                      "user[remember_me]": "0", "authenticity_token": self.token}))
        print("Login successful.")

    def _parseEpisode(self, episodeData: dict) -> Episode:
        episodeUrl = episodeData['sources'][0]['file']
        episodeBaseUrl = episodeUrl.split('index.m3u8')[0] + '/'

        episodeTitle = (episodeData['title'] + episodeData['description']
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

        episodeChunkListUrl = episodeBaseUrl + \
            self._validateResponse(
                self.session.get(episodeUrl), returnObj="m3u")[0]  # For now only use best quality

        rawChunkList = self._validateResponse(
            self.session.get(episodeChunkListUrl), returnObj="m3u")

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
        chunkList = [(chunk.split('?')[0].split('/')[-1], chunk.replace("../../../", episodeBaseUrl))
                     for chunk in rawChunkList]
        return self.Episode(episodeTitle, chunkList)

    def _setHeader(self, url: str):
        self.session.headers.update({"X-CSRF-Token": self.token, "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
                                     "Accept": "application/json, text/javascript, */*; q=0.01", "Referer": url, "X-Requested-With": "XMLHttpRequest", "Connection": "keep-alive"})

    @property
    def signInUrl(self) -> str:
        return self.baseUrl + self.signInPath

    @property
    def playlist(self) -> list:
        return self.currentPlaylist

    @property
    def token(self) -> str:
        return self.currentToken

    def setPlaylist(self, animeUrl):
        if re.match("https://(www\.)?anime-on-demand\.de/anime/\d+", animeUrl) is None:
            raise AoDDownloaderException(
                "Given url does not match a playlist url")
        response = self._validateResponse(
            self.session.get(animeUrl), returnObj='soup')
        stream = response.find('input', {'title': 'Deutschen Stream starten'}) if self.dubOnly else response.find(
            'input', {'title': 'Japanischen Stream mit Untertiteln starten'})
        if not stream or not stream['data-playlist']:
            raise AoDDownloaderException("Could not determine {lang} stream for {url}".format(
                lang="german" if self.dubOnly else "japanese", url=animeUrl))
        playlistUrl = f"https://www.anime-on-demand.de{stream['data-playlist']}"
        playlistData = self._validateResponse(
            self.session.get(playlistUrl), returnObj='json').get('playlist')

        self.currentPlaylist = [self._parseEpisode(
            episodeData) for episodeData in playlistData]

    def download(self):
        if not os.path.exists('downloads'):
            os.mkdir('downloads')
        for episode in self.playlist:
            if episode.exists:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                episodeChunks = []
                bar = ChargingBar(f"{episode.title}:",
                                  max=len(episode.chunkList))
                for chunkName, chunkUrl in episode.chunkList:
                    chunkFileName = f"{tmp}/{chunkName}"
                    with open(chunkFileName, 'wb') as chunk:
                        chunkResponse = self.session.get(chunkUrl)
                        if chunkResponse.status_code != 200:
                            raise AoDDownloaderException("Download failed")
                        chunk.write(chunkResponse.content)
                    ffmpegInput = ffmpeg.input(chunkFileName)
                    episodeChunks.append(ffmpegInput.video)
                    episodeChunks.append(ffmpegInput.audio)
                    bar.next()
                bar.finish()
                print(f"Converting {episode.title}... ")
                ffmpeg.concat(*episodeChunks, v=1,
                              a=1).output(episode.file).run(capture_stderr=True)
                print("Finished")


config = configparser.ConfigParser()
config.read_file(open(r'config.ini'))

# login credentials
username = (config.get("Credentials", "username")).encode('utf-8')
password = (config.get("Credentials", "password")).encode('utf-8')

# settings
# quality_options = ["bluray", "fullhd", "hd", "dvd", "sd", "mobil"]
# quality_option = str(config.get("Settings", "quality"))
# quality_option = quality_options.index(quality_option) + 2
# quality_option = quality_option

# sub = str(config.get("Settings", "sub"))
# if(sub == "yes"):
#     sub = True
# else:
#     sub = False

# episode_num_start = int(config.get("Settings", "episode_start"))
# episode_num_end = int(config.get("Settings", "episode_end"))

# get anime url
anime_url = input("Enter anime url: ")

# #download
# session = login(username, password)
# episodeList = get_playlist(session, anime_url)
# print(episodeList)

# download_episode(session, episodeList)

a = AoDDownloader(username, password)
a.setPlaylist(anime_url)
a.download()
