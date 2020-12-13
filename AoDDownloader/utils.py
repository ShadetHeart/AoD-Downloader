import click
import keyring
from keyring.errors import NoKeyringError

import AoDDownloader as AoD
from .config import Config


def create_downloader() -> AoD.AoDDownloader:
    config = Config()

    if config.username:
        if config.keyring:
            try:
                config.password = keyring.get_password(config.APPKEY, username=config.username)
            except NoKeyringError:
                click.echo(
                    "Keyring is not accessible.\n \"pip install dbus-python\" might fix this problem.")
        else:
            config.password = click.prompt('Password', hide_input=True)
    return AoD.AoDDownloader(config=config)


def create_login(use_keyring: bool = True):
    config = Config()
    config.username = click.prompt('Username')
    config.password = click.prompt('Password', hide_input=True)
    config.keyring = use_keyring
    try:
        aod = AoD.AoDDownloader(config=config)
    except AoD.AoDDownloaderException as e:
        click.echo(e)
        return
    if not aod.signed_in:
        click.echo("Login fehlgeschlagen.")
        return

    if use_keyring:
        try:
            keyring.set_password(config.APPKEY, username=config.username, password=config.password)
        except NoKeyringError:
            click.echo(
                f"""{click.style('Keyring is not accessible.', fg='red')}
"pip install dbus-python" might fix this problem.
Or use --no-keyring to enter password every time and disable keyring""")
    config.write()


def remove_login():
    config = Config()
    if config.username and config.keyring:
        try:
            keyring.delete_password(config.APPKEY, username=config.username)
        except NoKeyringError:
            click.echo(
                "Keyring is not accessible.\n \"pip install dbus-python\" might fix this problem.")
    config.username = None
    config.write()
