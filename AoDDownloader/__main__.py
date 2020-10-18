try:
    from AoDDownloader import cli
except ImportError:
    from . import cli

cli.cli()
