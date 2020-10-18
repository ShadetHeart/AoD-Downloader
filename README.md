# Anime on Demand Downloader 

**Currently refactoring in progress, the previous script can be found in the folder named "old"**

## Requirements
- [Anime on Demand](https://anime-on-demand.de) account  
  *Notice:* You can only donwload these episodes you are able to watch online
- [ffmpeg](https://ffmpeg.org/)
- [Python3.8](https://www.python.org/downloads/) or higher and if not installed with python [pip](https://pip.pypa.io/en/stable/installing/)

## Setup
Run `pip install git+https://github.com/ShadetHeart/AoD-Downloader.git` to install AoDDownloader with pip.  
If your system uses `pip3` for pip with python3 use this in the command above

## Usage
```
Usage: AoDDownloader [OPTIONS] COMMAND [ARGS]...

  AoDDownloader is a tool to download streams from anime-on-demand.de

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  download  Download an anime.
  login     Login to anime-on-demand.de and save credentials
  logout    Logout and remove all credentials
```

This project is licensed under the terms of the MIT license.
