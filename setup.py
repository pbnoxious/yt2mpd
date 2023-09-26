from setuptools import setup

setup(
    name="yt2mpd",
    version="0.2.0",
    description="Automatically download music via yt-dlp and play it in MPD",
    author="pbnoxious",
    license="GPLv3",
    packages=["yt2mpd"],
    scripts=["bin/yt2mpd"],
)
