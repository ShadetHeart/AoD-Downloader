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
@click.option('--no-buffer-output', 'noBufferOutput', is_flag=True,
              help='Disable buffering for progress output.')
@click.argument('url', default='')
@click.argument('password', default='')
def download(german, japanese, quality, verbose, url, password, noBufferOutput):
    """
    Download an anime.
    The files are downloaded in the current directory.
    """
    if password:
        downloader = create_downloader(password)
    else:
        downloader = create_downloader()
    if url:
        anime_url= url
    else:
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
        downloader.download(verbose, noBufferOutput)
    except _AoDDownloader.AoDDownloaderException as e:
        click.echo(f"{click.style('Error:', fg='red')} {e}")


@cli.command()
@click.option('--no-keyring', 'no_keyring', is_flag=True,
              help='Deactivate keyring option for systems who have no accessible keyring')
@click.argument('name', default='')
@click.argument('password', default='')
def login(no_keyring, name, password):
    """
    Login to anime-on-demand.de and save credentials
    """
    if name and password:
        create_login(not no_keyring, name, password)
    else:
        create_login(not no_keyring)


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
