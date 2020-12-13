from click_didyoumean import DYMGroup

import AoDDownloader as _AoDDownloader
from AoDDownloader.utils import *
from .quality import Quality


@click.group(cls=DYMGroup)
@click.version_option(version=_AoDDownloader.__version__, prog_name='AoDDownloader')
@click.pass_context
def cli(ctx):
    """
    AoDDownloader is a tool to download streams from anime-on-demand.de
    """
    ctx.obj = create_downloader()


@cli.command()
@click.option('-q', '--quality', 'quality', type=click.Choice([e.name for e in Quality]),
              help='Try downloading with this quality, else highest available',
              show_choices=True)
@click.option('-j', '--japanese', 'japanese', is_flag=True,
              help='Try downloading japanese audio with german subtitles.')
@click.option('-g', '--german', 'german', is_flag=True,
              help='Try downloading german audio.')
@click.pass_obj
def download(downloader, german, japanese, quality):
    """
    Download an anime.
    The files are downloaded in the current directory.
    """
    anime_url = click.prompt('Enter anime url to download')
    if quality:
        downloader.config.quality = Quality[quality]
    if german or japanese:
        downloader.config.japanese = japanese
        downloader.config.german = german
    try:
        downloader.set_playlist(anime_url)
        downloader.download()
    except _AoDDownloader.AoDDownloaderException as e:
        click.echo(f"{click.style('Error:', fg='red')} {e}")


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


@cli.group()
def config():
    """
    Configuration of AoDDownloader
    """


@config.command()
@click.pass_obj
def list(downloader):
    """
    List current config settings
    """
    click.echo(f"""Download german if available:\t{downloader.config.german or False}
Download japanese if available:\t{downloader.config.japanese or False}
Highest download quality:\t{downloader.config.quality.name if downloader.config.quality else "-"}""")


@config.command()
@click.pass_obj
def quality(downloader):
    """
    Change currently selected default download quality
    """
    downloader.config.setQuality()


@config.command()
@click.pass_obj
def languages(downloader):
    """
    Change currently selected languages to be downloaded
    """
    downloader.config.setLanguages()
