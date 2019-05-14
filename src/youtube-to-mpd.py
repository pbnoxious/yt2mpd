"""Scripts to automatically fetch youtube audio and play it via mpd."""

import os
import sys

def main():
    """Main entry point for the script."""
    pass

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
