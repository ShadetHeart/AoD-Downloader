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
    python_requires=">=3.8",
    install_requires=open("requirements.txt").read().split("\n"),
    entry_points='''
       [console_scripts]
       AoDDownloader=AoDDownloader.__main__:cli
   ''',
)