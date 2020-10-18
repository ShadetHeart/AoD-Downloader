from click_didyoumean import DYMGroup

import AoDDownloader as _AoDDownloader
from AoDDownloader.utils import *


@click.group(cls=DYMGroup)
@click.version_option(version=_AoDDownloader.__version__, prog_name='AoDDownloader')
@click.pass_context
def cli(ctx):
    """
    AoDDownloader is a tool to download streams from anime-on-demand.de
    """
    ctx.obj = create_downloader()


@cli.command()
@click.pass_obj
def download(downloader):
    """
    Download an anime.
    """
    anime_url = click.prompt('Enter anime url to download')
    downloader.set_playlist(anime_url)
    downloader.download()


@cli.command()
def login():
    """
    Login to anime-on-demand.de and save credentials
    """
    create_login()


@cli.command()
@click.pass_obj
def logout():
    """
    Logout and remove all credentials
    """
    remove_login()
