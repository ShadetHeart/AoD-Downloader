import json
import os
from pathlib import Path

import click

from .quality import Quality


class Config(object):
    APPKEY = "AoDDownloader"

    def __init__(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as config:
                json_config = json.load(config)
        else:
            json_config = {}

        self.username = json_config.get("username")
        self.german = json_config.get("german") or False
        self.japanese = json_config.get("japanese") or False
        self.quality = Quality[json_config.get("quality")] if json_config.get("quality") else None
        self.password = None

    def write(self):
        with open(self.path, 'w') as config_file:
            config_dict = {
                "username": self.username,
                "german": self.german,
                "japanese": self.japanese,
                "quality": self.quality.name if self.quality else ""
            }
            json.dump(config_dict, config_file)

    @property
    def path(self) -> str:
        app_path = os.getenv('APPDATA') + "/AoDDownloader" if os.name == 'nt' else str(Path.home().joinpath(".AoD"))
        if not os.path.exists(app_path):
            os.mkdir(app_path)
        return app_path + "/config.json"

    def setQuality(self):
        self.quality = Quality[
            click.prompt("Select the max wanted quality.", type=click.Choice([e.name for e in Quality]),
                         show_choices=True)]
        self.write()

    def setLanguages(self):
        self.japanese = click.confirm("Try downloading japanese audio with subtitles?")
        self.german = click.confirm("Try downloading german audio?")
        self.write()
        return self.japanese, self.german
