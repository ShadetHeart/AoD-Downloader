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
@click.option('-j', '--japanese', 'japanese', is_flag=True,
              help='Try downloading japanese audio with german subtitles.')
@click.option('-g', '--german', 'german', is_flag=True,
              help='Try downloading german audio.')
@click.pass_obj
def download(downloader, german, japanese):
    """
    Download an anime.
    The files are downloaded in the current directory.
    """
    anime_url = click.prompt('Enter anime url to download')
    downloader.set_playlist(anime_url, german=german, japanese=japanese)
    downloader.download()


@cli.command()
def login():
    """
    Login to anime-on-demand.de and save credentials
    """
    create_login()


@cli.command()
def logout():
    """
    Logout and remove all credentials
    """
    remove_login()
