import click
import keyring
from keyring.errors import NoKeyringError

import AoDDownloader as AoD

from .config import Config


def create_downloader() -> AoD.AoDDownloader:
    config = Config()

    if config.username:
        try:
            config.password = keyring.get_password(config.APPKEY, username=config.username)
        except NoKeyringError:
            click.echo(
                "Es konnte nicht auf den Keyring zugegriffen werden.\n Das Problem könnte mittels \"pip install dbus-python\" behoben werden.")
    return AoD.AoDDownloader(config=config)


def create_login():
    config = Config()
    config.username = click.prompt('Username')
    config.password = click.prompt('Password', hide_input=True)
    try:
        aod = AoD.AoDDownloader(config=config)
    except AoD.AoDDownloaderException as e:
        click.echo(e)
        return
    if not aod.signed_in:
        click.echo("Login fehlgeschlagen.")
        return

    try:
        keyring.set_password(config.APPKEY, username=config.username, password=config.password)
    except NoKeyringError:
        click.echo(
            "Es konnte nicht auf den Keyring zugegriffen werden.\n Das Problem könnte mittels \"pip install dbus-python\" behoben werden.")
    config.write()


def remove_login():
    config = Config()
    if config.username:
        try:
            keyring.delete_password(config.APPKEY, username=config.username)
        except NoKeyringError:
            click.echo(
                "Es konnte nicht auf den Keyring zugegriffen werden.\n Das Problem könnte mittels \"pip install dbus-python\" behoben werden.")
    config.username = None
    config.write()
