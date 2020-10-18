from os.path import join
from setuptools import setup

pkg = {}
mod = join('AoDDownloader', 'version.py')
exec(compile(open(mod).read(), mod, 'exec'), {}, pkg)

setup(
    name='AoDDownloader',
    version=pkg['__version__'],
    description='Download animes from Anime-on-Demand',
    url='https://github.com/ShadetHeart/AoD-Downloader',
    author='Shadet',
    license='MIT',
    packages=['AoDDownloader'],
    include_package_data=True,
    install_requires=[
        'Click == 7.1.2',
        'click-didyoumean',
        'requests >= 2.24.0',
        'beautifulsoup4 >= 4.9.3',
        'ffmpeg-python == 0.2.0',
        'progress >= 1.5',
        'keyring >= 21.4.0'
    ],
    entry_points='''
       [console_scripts]
       AoDDownloader=AoDDownloader.__main__:cli
   ''',
)