"""Scripts to automatically fetch youtube audio and play it via mpd."""

import os
import sys
import cliarguments
import config

def main():
    """Main entry point for the script."""
    cliargs = cliarguments.CliArguments() # read input
    print(cliargs.config_path)
    print(cliargs.song)

    settings = config.Config(cliargs.config_path) # read settings
    print(settings.config_path)

if __name__ == '__main__':
    sys.exit(main())


def download_song(identifier):
    """Get song from youtube"""
    os.system("youtube-dl -xq " + identifier)

def update_mpd():
    """Update MPD database"""
    os.system("mpc update")


def add_song_to_mpd(filename):
    """Update MPD database"""
    os.system("mpc add " + filename)

def remove_song(filename):
    """Check if song is still in playlist, otherwise remove it from disk"""
    os.system("mpc idle playlist") # this waits until something in the playlist is changed
    playlist=list(os.popen("mpc playlist"))
    #check if it is still there -> if not remove
