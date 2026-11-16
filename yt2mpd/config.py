"""Read and validate the local configuration before creating download files."""

import configparser
import logging
import os
from pathlib import Path

from .storage import download_root


class Config:
    def __init__(self, config_path):
        self.music_dir = os.environ.get("XDG_MUSIC_DIR")
        self.tmp_dir = "youtube"
        self.prune = False
        self.delete = False
        self.config_path = None
        if config_path is not None:
            self.config_path = Path(config_path).expanduser()
            if not self.config_path.is_file():
                raise ValueError("Specified config file was not found")
        else:
            config_home = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            )
            candidate = config_home / "yt2mpd" / "yt2mpd.conf"
            if candidate.is_file():
                self.config_path = candidate
        if self.config_path is not None:
            config = configparser.ConfigParser(interpolation=None)
            with self.config_path.open(encoding="utf-8") as source:
                config.read_file(source)
            self.music_dir = config.get("yt2mpd", "music_dir")
            self.tmp_dir = config.get("yt2mpd", "tmp_dir", fallback="youtube")
            self.prune = config.getboolean("yt2mpd", "prune", fallback=False)
            self.delete = config.getboolean("yt2mpd", "delete", fallback=False)
        else:
            logging.getLogger(__name__).warning(
                "No config file found, using default values"
            )
        music, _ = download_root(self.music_dir, self.tmp_dir)
        self.music_dir = str(music)
