"""
Read config from file and store in Config class
"""


import configparser
import logging
import os
import sys


class Config:
    """Stores and processes all settings

    Attributes:
        config_path: string holding the path of the config file
        music_dir: string to the mpd directory
        tmp_dir: string with the subdirectory for the youtube files
        (automatic removal (not for first version))
        (wanted audio format?)
    """

    def __init__(self, config_path):
        try:
            self.music_dir = os.environ["XDG_MUSIC_DIR"]
        except KeyError:
            self.music_dir = None
        self.tmp_dir = "youtube"
        self.prune = False
        self.delete = False
        self.config_path = None
        self.set_config_path(config_path)
        self.read_config()

    def set_config_path(self, config_path):
        """Determine path of config file, at the moment optimized for linux"""

        default_config_dirs = [
            # commented out because it breaks if not set
            # os.path.join(os.environ.get('XDG_CONFIG_HOME'), '.yt2mpt'),
            os.path.join(os.environ.get("HOME"), ".config", "yt2mpd")
        ]
        default_config_filename = "yt2mpd.conf"

        if config_path is not None:
            if os.path.isfile(config_path):
                self.config_path = config_path
            else:
                print("Error: Specified config file was not found")
                sys.exit(1)
        else:  # check some default locations if no config path was given
            for directory in default_config_dirs:
                try:
                    # this is ugly
                    path = os.path.join(directory, default_config_filename)
                    if os.path.isfile(path):
                        self.config_path = path
                        return  # if file was found, don't proceed
                except KeyError:
                    pass  # ignore not found errors?
            logging.warning("No config file found, using default values")

    def read_config(self):
        """Read the config file at given path"""
        if self.config_path is None:
            return  # use default values
        config = configparser.ConfigParser()
        config.read(self.config_path)

        self.music_dir = config.get("yt2mpd", "music_dir")
        if os.path.isdir(self.music_dir) is False:
            print("Error: specified MPD directory does not exist")
            sys.exit(1)

        self.tmp_dir = config.get("yt2mpd", "tmp_dir")
        full_tmp_path = os.path.join(self.music_dir, self.tmp_dir)
        if os.path.isdir(full_tmp_path) is False:
            os.makedirs(full_tmp_path)  # possible race condition
        self.prune = config.getboolean("yt2mpd", "prune", fallback=False)
        self.delete = config.getboolean("yt2mpd", "delete", fallback=False)
