"""Scripts to automatically fetch youtube audio and play it via mpd."""

import os
import sys
import cliarguments
import config

def download_song(identifier, tmp_dir):
    """Get song from youtube"""
    os.system("youtube-dl -xq --add-metadata -o '"
              + tmp_dir + os.path.sep + "%(title)s-%(id)s.%(ext)s' " + identifier)

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

def main():
    """Main entry point for the script."""
    cliargs = cliarguments.CliArguments() # read input
    settings = config.Config(cliargs.config_path) # read settings
    download_song(cliargs.song, settings.tmp_dir)
    # update_mpd()
    # add_song_to_mpd(

if __name__ == '__main__':
    sys.exit(main())
