import json
import os
from pathlib import Path

import click
import keyring
from keyring.errors import NoKeyringError

import AoDDownloader as AoD


def get_app_path(config: bool = False) -> str:
    app_path = os.getenv('APPDATA') + "/AoDDownloader" if os.name == 'nt' else str(Path.home().joinpath(".AoD"))
    if not os.path.exists(app_path):
        os.mkdir(app_path)
    return app_path + "/config.json" if config else app_path


def create_downloader() -> AoD.AoDDownloader:
    # TODO: Save username somewhere hidden
    # TODO: Save password in keyring
    # For now read from config. This wont work with installed version
    config_path = get_app_path(config=True)

    # login credentials
    username = None
    password = None

    if os.path.exists(config_path):
        with open(config_path, 'r') as config:
            json_config = json.load(config)
            username = json_config.get("username")
        if username:
            try:
                password = keyring.get_password("AoDDownloader", username=username)
            except NoKeyringError:
                click.echo(
                    "Es konnte nicht auf den Keyring zugegriffen werden.\n Das Problem könnte mittels \"pip install dbus-python\" behoben werden.")
    return AoD.AoDDownloader(username=username, password=password)


def create_login():
    aod = None
    username = click.prompt('Username')
    password = click.prompt('Password', hide_input=True)
    try:
        aod = AoD.AoDDownloader(username=username, password=password)
    except AoD.AoDDownloaderException:
        pass
    if not aod.signed_in:
        click.echo("Login fehlgeschlagen.")
        return

    with open(get_app_path(config=True), "w") as config:
        json.dump({"username": username}, config)
    try:
        keyring.set_password("AoDDownloader", username=username, password=password)
    except NoKeyringError:
        click.echo(
            "Es konnte nicht auf den Keyring zugegriffen werden.\n Das Problem könnte mittels \"pip install dbus-python\" behoben werden.")


def remove_login():
    app_path = get_app_path(config=True)
    if os.path.exists(app_path):
        with open(app_path, "r") as config:
            json_config = json.load(config)
            username = json_config.get("username")
        if username:
            try:
                password = keyring.delete_password("AoDDownloader", username=username)
            except NoKeyringError:
                click.echo(
                    "Es konnte nicht auf den Keyring zugegriffen werden.\n Das Problem könnte mittels \"pip install dbus-python\" behoben werden.")
        with open(app_path, "w") as config:
            json.dump({}, config)
