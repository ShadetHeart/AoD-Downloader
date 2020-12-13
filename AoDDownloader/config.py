import json
import os
from pathlib import Path

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
                "quality": self.quality.name
            }
            json.dump(config_dict, config_file)

    @property
    def path(self) -> str:
        app_path = os.getenv('APPDATA') + "/AoDDownloader" if os.name == 'nt' else str(Path.home().joinpath(".AoD"))
        if not os.path.exists(app_path):
            os.mkdir(app_path)
        return app_path + "/config.json"
