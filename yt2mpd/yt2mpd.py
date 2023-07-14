#!/usr/bin/env python3
"""Script to fetch audio from youtube and play it via mpd."""

import argparse
import os
import sys
import subprocess

from .config import Config


def parse_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(
        description="Fetch audio from youtube and play it via mpd.", prog="yt2mpd"
    )
    parser.add_argument("identifier", help="ID or URL of youtube video or playlist")
    parser.add_argument(
        "-c",
        "--config_path",
        metavar="config_path",
        help="Path to config file",
        default=None,
    )
    parser.add_argument(
        "-d",
        "--delete",
        action="store_true",
        help="Wait until tracks were removed from playlist and delete them directly.",
    )
    parser.add_argument(
        "-p",
        "--prune",
        action="store_true",
        help="Clean temporary directory on startup. Only files that are not queued are removed.",
    )
    return parser.parse_args()


def download(identifier, music_dir, tmp_dir):
    """Get song from youtube"""
    list_marker = "?list="
    if list_marker in identifier:  # download playlist -> put in subdir
        list_id = identifier.split(list_marker)[1]
        tmp_dir = os.path.join(tmp_dir, list_id)
        try:
            os.mkdir(os.path.join(music_dir, tmp_dir))
        except FileExistsError:
            pass  # ignore if directory already exists
    file_format = (
        "%(playlist_index)s-%(title)s-%(id)s.%(ext)s"  # move this to config file
    )
    audio_format = "vorbis"  # not needed at the moment, maybe allow this as option
    file_extension = ".ogg"  # would probably then be needed too
    output_string = os.path.join(music_dir, tmp_dir, file_format)
    print("Downloading from " + identifier + "\nto " + os.path.join(music_dir, tmp_dir))
    ytdl = subprocess.Popen(
        [
            "youtube-dl",
            "-i",
            "-x",
            "--add-metadata",
            "--rm-cache-dir",
            "-o",
            output_string,
            identifier,
        ],
        stdout=subprocess.PIPE,
    )
    stdout = ytdl.communicate()[0].decode("UTF-8")  # get string of stdout
    searchstring = "[ffmpeg] Adding metadata to "  # these lines contain the filenames
    filenames = [
        line[len(searchstring) + 1 : -1]
        for line in stdout.split("\n")
        if searchstring in line
    ]
    filenames = [os.path.relpath(f, music_dir) for f in filenames]
    return filenames


def update_mpd():
    """Update MPD database"""
    os.system("mpc update -q --wait")


def add_song_to_mpd(filename):
    """Add song at end of current playlist.
    Returns artist and title of added song as tuple"""
    os.system('mpc add "{}"'.format(filename))
    song_query = subprocess.Popen(
        ['mpc -f "%artist%\n%title%" listall "{}"'.format(filename)],
        stdout=subprocess.PIPE,
        shell=True,
    )
    (artist, title, _) = song_query.communicate()[0].decode("UTF-8").split("\n")
    return artist, title


def prune_dir(filenames, music_dir):
    """Remove all given files from the tmp_dir if not in current mpd playlist"""
    mpd_query = subprocess.Popen(
        ["mpc", "playlist", "-f", "%file%"], stdout=subprocess.PIPE
    )
    curr_playlist = mpd_query.communicate()[0].decode("UTF-8").split("\n")
    for f in set(filenames).difference(curr_playlist):  # only those not in playlist
        os.remove(os.path.join(music_dir, f))  # f contains tmp_dir
        filenames.remove(f)
    return filenames  # Return cleaned up list


def main():
    """Main entry point for the script."""
    cliargs = parse_args()  # read input
    settings = Config(cliargs.config_path)  # read settings

    if settings.prune or cliargs.prune:
        oldfiles = [
            os.path.join(settings.tmp_dir, f)
            for f in os.listdir(os.path.join(settings.music_dir, settings.tmp_dir))
        ]
        prune_dir(oldfiles, settings.music_dir)

    filenames = download(cliargs.identifier, settings.music_dir, settings.tmp_dir)
    print(f"{len(filenames)} Files were downloaded, now updating mpd and adding files")
    update_mpd()
    songtags = []
    for filename in filenames:
        songtags.append(add_song_to_mpd(filename))
    if len(filenames) == 1:
        (artist, title) = songtags[0]
        print('Song "{} - {}" was added to MPD successfully'.format(artist, title))
    else:
        print("{} songs were added successfully:".format(len(filenames)))
        for artist, title in songtags:
            print("  {} - {}".format(artist, title))

    if settings.delete or cliargs.delete:
        print("Waiting for songs to be removed from playlist")
        while filenames:  # not sure if this is wise, might wait for a long time ...
            os.system(
                "mpc idle playlist > /dev/null"
            )  # this waits until something in the playlist is changed
            filenames = prune_dir(filenames, settings.music_dir)


if __name__ == "__main__":
    sys.exit(main())
