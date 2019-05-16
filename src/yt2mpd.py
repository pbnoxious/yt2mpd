"""Scripts to automatically fetch youtube audio and play it via mpd."""

import os
import shlex
import sys
import cliarguments
import config

def download_song(identifier, music_dir, tmp_dir):
    """Get song from youtube"""
    file_format = "%(title)s-%(id)s.%(ext)s" # move this to config file
    audio_format = "vorbis" # same
    file_extension = ".ogg" # but more difficult here
    output_string = "'" + os.path.join(music_dir, tmp_dir) + os.path.sep + file_format + "' "
    os.system("youtube-dl -xq" +
              " --add-metadata" +
              " --audio-format " + audio_format +
              " --audio-quality 0" +
              " -o " + output_string +
              identifier
             )
    file_format = "%(title)s-%(id)s" # move this to config file
    output_string = "'" + tmp_dir + os.path.sep + file_format + "' "
    filename = os.popen("youtube-dl " +
                        " --get-filename" +
                        " -o " + output_string +
                        identifier
                       ).read()[:-1] # remove newline
    # filename.replace(" ", "\ ")
    return filename + file_extension

def update_mpd():
    """Update MPD database"""
    os.system("mpc update -q")


def add_song_to_mpd(filename):
    """Update MPD database"""
    os.system("mpc add " + shlex.quote(filename))

def remove_song(filename):
    """Check if song is still in playlist, otherwise remove it from disk"""
    os.system("mpc idle playlist") # this waits until something in the playlist is changed
    playlist=list(os.popen("mpc playlist"))
    #check if it is still there -> if not remove

def main():
    """Main entry point for the script."""
    cliargs = cliarguments.CliArguments() # read input
    settings = config.Config(cliargs.config_path) # read settings
    filename = download_song(cliargs.song, settings.music_dir, settings.tmp_dir)
    update_mpd()
    add_song_to_mpd(filename)

if __name__ == '__main__':
    sys.exit(main())
