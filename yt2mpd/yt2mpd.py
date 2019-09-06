#!/usr/bin/env python3
"""Scripts to automatically fetch youtube audio and play it via mpd."""

import argparse
import os
import sys
import subprocess

import config

def parse_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(
        description = "Fetch audio from youtube and play it via mpd.",
        prog = "yt2mpd"
        )
    parser.add_argument('identifier',
                        help="ID or URL of youtube video or playlist")
    parser.add_argument("-c", metavar="config_path",
                        help="Path to config file")
    return parser.parse_args()

def download_song(identifier, music_dir, tmp_dir):
    """Get song from youtube"""
    file_format = "%(playlist_index)s-%(title)s-%(id)s.%(ext)s" # move this to config file
    audio_format = "vorbis" # not needed at the moment, maybe allow this as option
    file_extension = ".ogg" # would probably then be needed too
    output_string = os.path.join(music_dir, tmp_dir, file_format)
    print("Downloading from " + identifier + "\nto " + os.path.join(music_dir, tmp_dir))
    ytdl = subprocess.Popen(["youtube-dl", "-x", "--add-metadata",
                             "-o", output_string, identifier
                            ],
                            stdout=subprocess.PIPE
                           )
    stdout = ytdl.communicate()[0].decode('UTF-8') # get string of stdout
    searchstring = "[ffmpeg] Adding metadata to " # these lines contain the filenames
    filenames = [line[len(searchstring)+1:-1] for line in stdout.split("\n") if searchstring in line]
    filenames = [os.path.relpath(f, music_dir) for f in filenames]
    return filenames

def update_mpd():
    """Update MPD database"""
    os.system("mpc update -q --wait")

def add_song_to_mpd(filename):
    """Update MPD database"""
    os.system('mpc add "{}"'.format(filename))

def remove_song(filename):
    """Check if song is still in playlist, otherwise remove it from disk"""
    os.system("mpc idle playlist") # this waits until something in the playlist is changed
    playlist=list(os.popen("mpc playlist"))
    #check if it is still there -> if not remove

def main():
    """Main entry point for the script."""
    cliargs = parse_args() # read input
    settings = config.Config(cliargs.config_path) # read settings
    filenames = download_song(cliargs.identifier, settings.music_dir, settings.tmp_dir)
    print("Files were downloaded, now updating mpd and adding files")
    update_mpd()
    for filename in filenames:
        add_song_to_mpd(filename)
    if len(filenames) == 1:
        print("Song was added to MPD successfully")
    else:
        print("{} songs were added successfully".format(len(filenames)))

if __name__ == '__main__':
    sys.exit(main())
