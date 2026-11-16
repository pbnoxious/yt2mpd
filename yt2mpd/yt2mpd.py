#!/usr/bin/env python3
"""Fetch audio with yt-dlp and add it to the MPD queue."""

import argparse
import json
import re
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit

from .config import Config
from .storage import DownloadStore


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch audio from youtube and play it via mpd.", prog="yt2mpd"
    )
    parser.add_argument("identifier", help="ID or URL of youtube video or playlist")
    parser.add_argument(
        "-c", "--config_path", metavar="config_path", help="Path to config file"
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Wait for downloaded tracks to leave the queue, then delete owned files.",
    )
    parser.add_argument(
        "-p",
        "--prune",
        action="store_true",
        help="Remove owned downloads that are not in the MPD queue before downloading.",
    )
    return parser.parse_args()


def download(identifier, music_dir, tmp_dir):
    """Use machine-readable paths, with no external downloader configuration."""
    playlist_ids = parse_qs(urlsplit(identifier).query, keep_blank_values=True).get(
        "list", []
    )
    if playlist_ids and (
        len(playlist_ids) != 1
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", playlist_ids[0])
    ):
        raise ValueError(
            "Invalid playlist ID: only letters, digits, '_' and '-' are allowed"
        )
    store = DownloadStore(music_dir, tmp_dir)
    batch = store.new_batch(playlist_ids[0] if playlist_ids else None)
    template = str(batch / "%(playlist_index)s-%(title)s-%(id)s.%(ext)s")
    print(f"Downloading from {identifier}\nto {batch}")
    result = subprocess.run(
        [
            "yt-dlp",
            "--ignore-config",
            "-x",
            "--add-metadata",
            "--no-simulate",
            "--print",
            "after_move:%(filepath)j",
            "-o",
            template,
            "--",
            identifier,
        ],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        check=True,
    )
    filenames = [json.loads(line) for line in result.stdout.splitlines() if line]
    return store.record(batch, filenames)


def update_mpd():
    subprocess.run(["mpc", "update", "-q", "--wait"], check=True)


def add_song_to_mpd(filename):
    """Pass media filenames as literal arguments, never as shell source."""
    subprocess.run(["mpc", "add", "--", filename], check=True)
    result = subprocess.run(
        ["mpc", "-f", "%artist%\n%title%", "listall", "--", filename],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        check=True,
    )
    tags = result.stdout.splitlines()
    if len(tags) != 2:
        raise ValueError("MPD returned unexpected artist/title information")
    return tuple(tags)


def prune_dir(store, filenames):
    """A failed MPD query raises before any deletion is attempted."""
    result = subprocess.run(
        ["mpc", "playlist", "-f", "%file%"],
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return store.prune(filenames, set(result.stdout.splitlines()))


def main():
    cliargs = parse_args()
    settings = Config(cliargs.config_path)
    store = DownloadStore(settings.music_dir, settings.tmp_dir)
    if settings.prune or cliargs.prune:
        prune_dir(store, store.owned_files())

    filenames = download(cliargs.identifier, settings.music_dir, settings.tmp_dir)
    print(f"{len(filenames)} files were downloaded, now updating MPD and adding files")
    update_mpd()
    for filename in filenames:
        artist, title = add_song_to_mpd(filename)
        print(f'Song "{artist} - {title}" was added to MPD successfully')

    if settings.delete or cliargs.delete:
        print("Waiting for songs to be removed from the queue")
        # Query before waiting too: a track can leave the queue before idle starts.
        filenames = prune_dir(store, filenames)
        while filenames:
            subprocess.run(
                ["mpc", "idle", "playlist"], stdout=subprocess.DEVNULL, check=True
            )
            filenames = prune_dir(store, filenames)


if __name__ == "__main__":
    sys.exit(main())
