import configparser
import logging
import os

def get_config_path():
    """Determine path of config file, at the moment optimized for linux"""
    try:
        configfolder = os.environ['XDG_CONFIG_HOME']
    except KeyError:
        configfolder = os.environ['HOME'] + "/.config"
    configpath = configfolder + "/yt2mpd/yt2mpd.conf"
    if not (os.path.isfile(configpath)):
        logging.info("Config file not found, using default settings")
        configpath = ''
    return configpath

def read_config(configpath):
    """Read the config file at given path"""
    if (configpath == ''):
        break
    config = configparser.ConfigParser()
    config.read(configpath)
