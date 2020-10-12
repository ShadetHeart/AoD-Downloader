#!/usr/bin/env python3

import requests
import os
import re
import shutil
import configparser
import json
import pprint
from bs4 import BeautifulSoup
from ffmpeg import FFmpeg


def login(username: str, password: str) -> requests.Session:
    # create session cookies
    url = "https://www.anime-on-demand.de/users/sign_in"

    session = requests.Session()

    response = session.get(url)
    soup = BeautifulSoup(response.text, features="html.parser")

    # create login auth token
    token = soup.find('input', {'name': 'authenticity_token'})['value']

    # login
    login = {"utf8": "&#x2713;", "user[login]": username, "user[password]": password,
             "user[remember_me]": "0", "authenticity_token": token}
    response = session.post(url, data=login)
    return session


def get_playlist(session: requests.Session, anime_url: str) -> list:

    response = session.get(anime_url)
    soup = BeautifulSoup(response.text, features="html.parser")

    csrf_token = soup.find('meta', {'name': 'csrf-token'})['content']

    ger_stream = soup.find('input', {'title': 'Deutschen Stream starten'})
    jap_stream = soup.find(
        'input', {'title': 'Japanischen Stream mit Untertiteln starten'})

    playlist_path = ger_stream['data-playlist'] if (
        not sub) and ger_stream is not None else jap_stream['data-playlist'] if jap_stream is not None else None
    if not playlist_path:
        print('Unable to find playlist')
        exit(1)

    playlist_url = f"https://www.anime-on-demand.de{playlist_path}"
    print(f"Found playlist: {playlist_url}")

    # download playlist info
    session.headers.update({"X-CSRF-Token": csrf_token, "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",
                            "Accept": "application/json, text/javascript, */*; q=0.01", "Referer": anime_url, "X-Requested-With": "XMLHttpRequest", "Connection": "keep-alive"})
    response = session.get(playlist_url)

    # if response.status_code == 200:
    #     return json.loads(response.text).get('playlist')
    # return None
    return response.text


def download_episode(session: requests.Session, episodeList):
    refactor_chunklist_url = ''
    refactor_chunklist_response = ''

    def parse_m3u(m3uContent: str) -> str:
        # Only return highest Quality for now
        for line in m3uContent.split("\n"):
            if not line.startswith('#'):
                return line.strip()
        return ""

    episodeListList = json.loads(episodeList).get('playlist')

    for episode in episodeListList:
        episodeUrl = episode['sources'][0]['file']
        episodeBaseUrl = episodeUrl[:(episodeUrl.find('index.m3u8'))] + "/"
        episodeTitle = (episode['title'] + episode['description']
                        ).replace(" - ", "_").replace(" ", "_").replace(",", "")

        episodeChunkListUrl = episodeBaseUrl + parse_m3u(session.get(episodeUrl).text)

        refactor_chunklist_url = episodeChunkListUrl
        # get chunklist
        episodeChunkList = session.get(episodeChunkListUrl)
        print(episodeChunkList.text)
        # episodeChunkList = episode_chunklist.text

        # TODO: Redo download and transcode
        # maybe use python-ffmpeg to reduce usage of os.system
        # FFmpeg().option('f', 'concat').input(tmp/chunklist).output(episode_title + '.mkv', c='copy')

    # return

    # episode_counter = 0
    # episode_list = episodeList

    # while(episode_list.find("title") != -1):

    #     episode_counter = episode_counter + 1

    #     # get episode chunklist sources url
    #     episode_list = episode_list[(episode_list.find("file")+7):]
    #     episode_url = episode_list[:episode_list.find('"')]
    #     episode_url = episode_url.replace("\\u0026", "&")

    #     # get episode title
    #     episode_list = episode_list[(episode_list.find("title")+8):]
    #     episode_title = episode_list[:episode_list.find('"')]
    #     episode_title = episode_title.replace(" ", "_")

    #     if(episode_counter < episode_num_start):
    #         continue

    #     if(episode_counter > episode_num_end):
    #         break

    #     # get chunklist url
    #     episode_chunklist_url = session.get(episode_url)
    #     episode_chunklist_url = episode_chunklist_url.text

    #     # fetch quality options
    #     quality_options = re.findall("BANDWIDTH.*", episode_chunklist_url)

    #     # quality option setting
    #     quality_counter = 1

    #     # streamlock or cloudfround differentiation
    #     if("streamlock" in episode_url):
    #         while(quality_counter < quality_option):
    #             episode_chunklist_url = episode_chunklist_url[(
    #                 episode_chunklist_url.find("RESOLUTION")+10):]
    #             quality_counter = quality_counter + 1
    #         episode_chunklist_url = episode_chunklist_url[(episode_chunklist_url.find(
    #             "chunklist")):(episode_chunklist_url.find('.m3u8')+5)]
    #         episode_chunklist_url = episode_url[:(
    #             episode_url.find(".smil")+6)] + episode_chunklist_url
    #     else:
    #         while(quality_counter < quality_option):
    #             episode_chunklist_url = episode_chunklist_url[(
    #                 episode_chunklist_url.find("RESOLUTION")+10):]
    #             quality_counter = quality_counter + 1
    #         episode_chunklist_url = episode_chunklist_url[(episode_chunklist_url.find(
    #             "CODECS=")+31):(episode_chunklist_url.find("Id=")+23)]
    #         episode_chunklist_url = episode_url[:(
    #             episode_url.find('index.m3u8'))]+"/" + episode_chunklist_url

    #     # get chunklist
    #     episode_chunklist = session.get(episode_chunklist_url)
    #     episode_chunklist = episode_chunklist.text

    #     print(refactor_chunklist_url)
    #     print(episode_chunklist_url)

        # print("\n\n\n")
        # print(refactor_chunklist_response)
        # print(episode_chunklist)

        # # clean chunklist
        # if("streamlock" in episode_url):
        #     chunks = re.findall("media.*", episode_chunklist)
        #     episode_chunklist = ""
        #     for line in chunks:
        #         episode_chunklist = episode_chunklist + \
        #             (episode_url[:(episode_url.find(".smil")+6)] + line) + "\n"

        # else:
        #     chunks = re.findall("..\/..\/..\/.*", episode_chunklist)
        #     episode_chunklist = ""
        #     for line in chunks:
        #         episode_chunklist = episode_chunklist + \
        #             (episode_url[:(episode_url.find('index.m3u8'))
        #                          ] + line[8:]) + "\n"

        # # check if episode is already downloaded
        # if(os.path.exists(episode_title + ".mkv")):
        #     continue

        # # download episode
        # downloaded_chunks = 0
        # download_percentage = 0

        # # create tmp directory for chunks
        # if(not os.path.exists("tmp")):
        #     os.mkdir("tmp")

        # for url in episode_chunklist.splitlines():
        #     # download chunk
        #     with open("tmp/" + str(downloaded_chunks) + ".ts", "wb") as file:
        #         response = requests.get(url)
        #         file.write(response.content)

        #     downloaded_chunks = downloaded_chunks + 1
        #     download_percentage = (downloaded_chunks)/(len(chunks))*100
        #     download_percentage = format(download_percentage, ".2f")

        #     if os.name == "nt":
        #         os.system('cls')
        #     else:
        #         os.system('clear')

        #     print("downloading episode " + str(episode_counter))
        #     print(download_percentage)

        # # create chunklist for ffmpeg
        # with open("tmp/chunklist", "w") as file:
        #     for i in range(0, int(len(chunks))):
        #         file.write("file '" + str(i) + ".ts'" + "\n")

        # # merge to video
        # print("creating video")
        # os.system('ffmpeg -f "concat" -i "tmp/chunklist" -c copy "' +
        #           episode_title + '.mkv"')

        # # cleanup
        # shutil.rmtree("tmp")


if os.name == "nt":
    os.system('cls')
else:
    os.system('clear')

# read config file file
config = configparser.ConfigParser()
config.read_file(open(r'config.ini'))

# login credentials
username = (config.get("Credentials", "username")).encode('utf-8')
password = (config.get("Credentials", "password")).encode('utf-8')

# settings
quality_options = ["bluray", "fullhd", "hd", "dvd", "sd", "mobil"]
quality_option = str(config.get("Settings", "quality"))
quality_option = quality_options.index(quality_option) + 2
quality_option = quality_option

sub = str(config.get("Settings", "sub"))
if(sub == "yes"):
    sub = True
else:
    sub = False

episode_num_start = int(config.get("Settings", "episode_start"))
episode_num_end = int(config.get("Settings", "episode_end"))

# get anime url
anime_url = input("Enter anime url: ")

# #download
session = login(username, password)
episodeList = get_playlist(session, anime_url)
download_episode(session, episodeList)
