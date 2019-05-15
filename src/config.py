import configparser
import logging
import os

class Settings:
    """Stores and processes all settings

    Attributes:
        config_path: string holding the path of the config file
        music_dir: string to the mpd directory
        tmp_dir: string with the subdirectory for the youtube files
        (automatic removal (not for first version))
        (wanted audio format?)
    """


    def __init__(self, config_path):
        self.music_dir = os.environ['XDG_MUSIC_DIR']
        self.tmp_dir = "youtube"
        self.config_path = self.set_config_path(config_path)

    @staticmethod
    def set_config_path(config_path):
        """Determine path of config file, at the moment optimized for linux"""
        if not os.path.isfile(config_path):
            try:
                config_dir= os.environ['XDG_CONFIG_HOME']
            except KeyError:
                config_dir = os.environ['HOME'] + "/.config"
            config_path = config_dir + "/yt2mpd/yt2mpd.conf"
            if not os.path.isfile(config_path):
                logging.info("Config file not found using default settings")
                exit (-1) # how to get global settings path?
        return config_path

    def read_config(self):
        """Read the config file at given path"""
        if self.config_path is None:
            return # probably use "class" with default values -> don't overwrite
        config = configparser.ConfigParser()
        config.read(self.config_path)
