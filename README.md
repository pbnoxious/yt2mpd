# yt2mpd
> youtube to mpd script

Small tool that makes playing audio from youtube videos in mpd possible.
Uses youtube-dl to download the requested audio to a temporary folder.
Adds the successfully downloaded files to the current MPD playlist via mpc.

## Installation

Download the source code and run
```sh
pip install .
```

There is also a package build for an arch linux package hosted that can be found [here](https://raw.githubusercontent.com/pbnoxious/yt2mpd-pkg/master/PKGBUILD)


## Configuration

If the local MPD folder is not `$XDG_MUSIC_DIR` you will have to specify it in a config file.
By default the program searches for a config file named yt2mpd.conf in either `$XDG_CONFIG_HOME/yt2mpd` or `~/.config/yt2mpd` but you can also pass a custom location with the --config option.
See the ``doc/yt2mpd.conf`` file for the config options and default values


## Issues and wanted features

Add volatility, i.e. files are deleted automatically after they have been listened to.


## License

Distributed under the GPL3 license.
See ``LICENSE`` for more information.
