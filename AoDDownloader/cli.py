from click_didyoumean import DYMGroup

import AoDDownloader as _AoDDownloader
from AoDDownloader.utils import *
from .quality import Quality


@click.group(cls=DYMGroup)
@click.version_option(version=_AoDDownloader.__version__, prog_name='AoDDownloader')
def cli():
    """
    AoDDownloader is a tool to download streams from anime-on-demand.de
    """


@cli.command()
@click.option('-v', '--verbose', 'verbose', is_flag=True,
              help='Verbose output')
@click.option('-q', '--quality', 'quality', type=click.Choice([e.name for e in Quality]),
              help='Try downloading with this quality, else highest available',
              show_choices=True)
@click.option('-j', '--japanese', 'japanese', is_flag=True,
              help='Try downloading japanese audio with german subtitles.')
@click.option('-g', '--german', 'german', is_flag=True,
              help='Try downloading german audio.')
def download(german, japanese, quality, verbose):
    """
    Download an anime.
    The files are downloaded in the current directory.
    """
    downloader = create_downloader()
    anime_url = click.prompt('Enter anime url or id to download')
    if quality:
        if verbose:
            click.echo(f"Override quality settings")
        downloader.config.quality = Quality[quality]
    if german or japanese:
        if verbose:
            click.echo(f"Override language settings")
        downloader.config.japanese = japanese
        downloader.config.german = german
    try:
        downloader.set_playlist(anime_url, verbose)
        downloader.download(verbose)
    except _AoDDownloader.AoDDownloaderException as e:
        click.echo(f"{click.style('Error:', fg='red')} {e}")


@cli.command()
@click.option('--no-keyring', 'no_keyring', is_flag=True,
              help='Deactivate keyring option for systems who have no accessible keyring')
def login(no_keyring):
    """
    Login to anime-on-demand.de and save credentials
    """
    create_login(use_keyring=not no_keyring)


@cli.command()
def logout():
    """
    Logout and remove all credentials
    """
    remove_login()


@cli.group()
def config():
    """
    Configuration of AoDDownloader
    """


@config.command()
def list():
    """
    List current config settings
    """
    downloader = create_downloader()
    click.echo(f"""Download german if available:\t{downloader.config.german or False}
Download japanese if available:\t{downloader.config.japanese or False}
Highest download quality:\t{downloader.config.quality.name if downloader.config.quality else "-"}""")


@config.command()
def quality():
    """
    Change currently selected default download quality
    """
    create_downloader().config.setQuality()


@config.command()
def languages(downloader):
    """
    Change currently selected languages to be downloaded
    """
    create_downloader().config.setLanguages()
