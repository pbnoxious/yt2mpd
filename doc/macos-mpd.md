# Set up MPD on macOS

MPD is a music player that runs as a background service. `mpc` controls its queue and playback.
`yt2mpd` downloads audio with `yt-dlp`, then adds the files to that queue.
It does not start playback itself.

These instructions run MPD under your own macOS account, with CoreAudio output.
The server listens only on `127.0.0.1:6600`, not on your local network.
Other programs on your Mac can still control this local server.

This guide was checked against the Homebrew formula and MPD documentation, not a live MPD installation.
No service was started during development of this guide.

## Install the tools

Install MPD, its client, the downloader, and the audio conversion tool:

```sh
brew install mpd mpc yt-dlp ffmpeg
```

From the yt2mpd checkout, install the Python command:

```sh
uv tool install --reinstall .
yt2mpd --help
```

Keep these tools current. The Python environment created by uv does not restrict file or network access.

## Create the directories

Create the music, configuration, and MPD state directories:

```sh
mkdir -p "$HOME/Music" "$HOME/.config/mpd" "$HOME/.local/state/mpd/playlists" "$HOME/.config/yt2mpd"
```

If you already use another music directory, substitute that path in both configuration files below.
Do not replace an existing MPD configuration without reviewing it first.

## Configure MPD

Save this content as `~/.config/mpd/mpd.conf`:

```conf
music_directory "~/Music"
playlist_directory "~/.local/state/mpd/playlists"
db_file "~/.local/state/mpd/database"
state_file "~/.local/state/mpd/state"
sticker_file "~/.local/state/mpd/sticker.sql"
log_file "~/.local/state/mpd/mpd.log"
pid_file "~/.local/state/mpd/mpd.pid"

bind_to_address "127.0.0.1"
port "6600"
follow_outside_symlinks "no"
follow_inside_symlinks "no"
zeroconf_enabled "no"

audio_output {
    type "osx"
    name "CoreAudio"
    mixer_type "software"
}
```

The `osx` output uses the Mac's default audio device.
MPD creates its database and state files in the directories from the previous step.
Do not create empty database files yourself.

MPD normally finds this configuration under `~/.config/mpd`.
If you set `XDG_CONFIG_HOME`, use its `mpd/mpd.conf` location instead.
The Homebrew service must find the same configuration as your terminal session.

## Configure yt2mpd

Save this content as `~/.config/yt2mpd/yt2mpd.conf`:

```ini
[yt2mpd]
music_dir = ~/Music
tmp_dir = youtube
prune = False
delete = False
```

The `music_dir` path must match MPD's `music_directory`.
`yt2mpd` expands `~` to your home directory in this value.
Do not put comments after configuration values.

If you set `XDG_CONFIG_HOME`, save the file under its `yt2mpd` directory instead.
You can also select a file explicitly with `yt2mpd -c /absolute/path/to/yt2mpd.conf VIDEO_URL`.

## Test MPD in the foreground

If MPD already runs, stop that instance before starting another one on port 6600.
Start MPD in a terminal:

```sh
mpd --no-daemon "$HOME/.config/mpd/mpd.conf"
```

Keep this terminal open. In a second terminal, select the local server and scan your music directory:

```sh
export MPD_HOST=127.0.0.1
export MPD_PORT=6600
mpc status
mpc update --wait
mpc outputs
```

If the output is disabled, enable its ID with `mpc enable ID`.
If MPD reports an error, read `~/.local/state/mpd/mpd.log`.
If MPD cannot read your music, review macOS privacy permissions for the terminal or service that runs it.

## Start MPD at login

After the foreground test succeeds, press Ctrl-C in its terminal to stop that instance.
Then start MPD as a user service:

```sh
brew services start mpd
brew services list
mpc status
```

Do not use `sudo`. MPD must run under the same account that owns the downloaded files.
Homebrew currently starts `mpd --no-daemon` without an explicit configuration path.
If service behavior differs from the foreground test, make sure that it finds the configuration above.

To stop the service later, run:

```sh
brew services stop mpd
```

## Download and play audio

Use a video that you have permission to download. Replace `VIDEO_ID` with its actual ID:

```sh
export MPD_HOST=127.0.0.1
export MPD_PORT=6600
yt2mpd 'https://www.youtube.com/watch?v=VIDEO_ID'
mpc playlist
mpc play
```

`yt2mpd` waits for the MPD database update before adding downloaded files.
`mpc play` starts playback. Use `mpc pause` or `mpc stop` to stop listening.
To remove a particular queue entry, use `mpc del POSITION` with its number from `mpc playlist`.

## Optional cleanup

Leave cleanup disabled until you want automatic deletion.
Playback finishing does not normally remove a song from the MPD queue.
With `--delete`, yt2mpd waits until the downloaded songs leave the queue, then deletes eligible files.
You can remove queue entries yourself or enable MPD's consume mode with `mpc consume on`.
Consume mode changes the whole queue, not just yt2mpd downloads.

Use `--prune` to remove eligible downloads absent from the queue before a new download.
If an MPD command fails, cleanup stops.
It considers only unchanged files recorded by yt2mpd 0.3 in its private download directories.
It leaves unrelated files, pre-0.3 downloads, failed downloads, edited files, replacements, and links alone.
It leaves the small receipt files and batch directories in place.

The receipts are local bookkeeping, not a security boundary against other programs running as your account.
Do not share the download directory with untrusted writers or edit it while cleanup runs.
`yt2mpd` ignores external yt-dlp configuration to prevent hidden options from changing its behavior.
Downloads that require cookies or other custom downloader configuration are not supported by this wrapper.

## Sources

The [Homebrew MPD formula](https://formulae.brew.sh/formula/mpd) documents installation and service commands.
Its [source](https://raw.githubusercontent.com/Homebrew/homebrew-core/HEAD/Formula/m/mpd.rb) shows the service command and macOS output test.
The [MPD user manual](https://mpd.readthedocs.io/en/stable/user.html) describes configuration and local music directories.
The [mpc manual](https://www.musicpd.org/doc/mpc/html/) describes queue commands, playback, and connection options.
