# yt2mpd
> youtube to mpd script

Small tool that makes playing audio from youtube videos in mpd possible.
Uses yt-dlp to download the requested audio to a temporary folder.
Adds the successfully downloaded files to the current MPD playlist via mpc.

## Installation

From the source checkout, install the command with uv:
```sh
uv tool install .
yt2mpd --help
```

The command also needs `yt-dlp`, `ffmpeg`, `mpc`, and a running MPD server.
See [the macOS setup guide](doc/macos-mpd.md) for installation, configuration, and playback instructions.

A separate [Arch Linux package recipe](https://raw.githubusercontent.com/pbnoxious/yt2mpd-pkg/master/PKGBUILD) is also available.
That external recipe was not part of the local security review.


## Configuration

If your MPD music directory differs from `$XDG_MUSIC_DIR`, set `music_dir` in a configuration file.
If `XDG_CONFIG_HOME` is set, the program reads `$XDG_CONFIG_HOME/yt2mpd/yt2mpd.conf`.
Otherwise, it reads `~/.config/yt2mpd/yt2mpd.conf`.
Use `-c /path/to/yt2mpd.conf` to select another file.
See `doc/yt2mpd.conf` for an example with the default cleanup values.


## Downloads and cleanup

Each download uses a separate directory under `music_dir/tmp_dir`.
The temporary directory must be a relative subdirectory of the music directory, without `..` components.
Playlist IDs cannot contain path separators or traversal components.
The downloader ignores external yt-dlp configuration and reports final paths as JSON.

Deletion is off by default. Use `--prune` for startup cleanup or `--delete` to wait for tracks to leave the MPD queue.
Cleanup only removes unchanged files recorded by this tool, and stops on MPD failures.
It preserves unowned files, files from versions before 0.3, and incomplete downloads.
Do not share download directories with untrusted writers.

## Development

Run the offline regression tests without MPD, yt-dlp, or network access:

```sh
python3 -m unittest discover -s tests -v
```


## License

Distributed under the GPL3 license.
See ``LICENSE`` for more information.
