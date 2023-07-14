from setuptools import setup

setup(
    name="yt2mpd",
    version="0.1.2",
    description="Automatically download music via youtube-dl and play it in MPD",
    author="pbnoxious",
    license="GPLv3",
    packages=["yt2mpd"],
    scripts=["bin/yt2mpd"],
)
