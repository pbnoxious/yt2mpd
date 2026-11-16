"""Confined download directories and receipts for conservative cleanup."""

import json
import tempfile
from pathlib import Path

RECEIPT = ".yt2mpd.json"


def download_root(music_dir, tmp_dir):
    """Reject traversal, absolute paths and symlink escapes before any writes."""
    if not music_dir:
        raise ValueError("Set music_dir in yt2mpd.conf or set XDG_MUSIC_DIR")
    music = Path(music_dir).expanduser().resolve(strict=True)
    if not music.is_dir():
        raise ValueError("music_dir must be an existing directory")
    relative = Path(tmp_dir)
    if relative.is_absolute() or ".." in relative.parts or relative == Path("."):
        raise ValueError(
            "tmp_dir must be a nonempty relative subdirectory without '..'"
        )
    root = (music / relative).resolve()
    if not root.is_relative_to(music) or root == music:
        raise ValueError("tmp_dir must stay inside music_dir")
    return music, root


def identity(path):
    """A replaced, edited or hard-linked file is no longer eligible for deletion."""
    if path.is_symlink() or not path.is_file():
        return None
    info = path.stat()
    if info.st_nlink != 1:
        return None
    return [info.st_dev, info.st_ino, info.st_ctime_ns]


class DownloadStore:
    """Track files created in a private directory for each successful download."""

    def __init__(self, music_dir, tmp_dir):
        self.music, self.root = download_root(music_dir, tmp_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def new_batch(self, playlist_id=None):
        if self.root.resolve() != self.root:
            raise ValueError("Download root changed to a symlink")
        prefix = "download-" + (playlist_id + "-" if playlist_id else "")
        return Path(tempfile.mkdtemp(prefix=prefix, dir=self.root))

    def record(self, batch, filenames):
        entries = {}
        for filename in filenames:
            if not isinstance(filename, str) or "\n" in filename or "\r" in filename:
                raise ValueError("Downloader returned an invalid filename")
            path = Path(filename)
            if not path.is_absolute() or path.parent != batch or path.is_symlink():
                raise ValueError(
                    "Downloader returned a path outside its download directory"
                )
            resolved = path.resolve(strict=True)
            if resolved.parent != batch or not resolved.is_relative_to(self.root):
                raise ValueError("Downloaded file escaped the download root")
            file_identity = identity(path)
            if file_identity is None or path.name == RECEIPT:
                raise ValueError(
                    "Downloader did not produce a regular, private media file"
                )
            entries[path.name] = file_identity
        # A failed or interrupted download has no receipt and is never auto-deleted.
        with (batch / RECEIPT).open("x", encoding="utf-8") as receipt:
            json.dump(entries, receipt)
        return [str((batch / name).relative_to(self.music)) for name in entries]

    def owned_files(self):
        """Validate all receipts before returning any deletion candidates."""
        owned = {}
        for receipt in self.root.glob("download-*/" + RECEIPT):
            batch = receipt.parent
            if batch.is_symlink() or receipt.is_symlink():
                raise ValueError("Refusing a symlinked download receipt")
            if batch.resolve().parent != self.root:
                raise ValueError("Download receipt escaped the download root")
            with receipt.open(encoding="utf-8") as source:
                entries = json.load(source)
            if not isinstance(entries, dict):
                raise TypeError("Invalid download receipt")
            for name, file_identity in entries.items():
                if (
                    not name
                    or Path(name).name != name
                    or name in (".", "..", RECEIPT)
                    or "\n" in name
                    or "\r" in name
                    or not isinstance(file_identity, list)
                    or len(file_identity) != 3
                    or not all(type(value) is int for value in file_identity)
                ):
                    raise ValueError("Invalid file entry in download receipt")
                path = batch / name
                if identity(path) == file_identity:
                    owned[str(path.relative_to(self.music))] = file_identity
        return owned

    def prune(self, candidates, playlist):
        """Delete only unchanged receipted files absent from a successful MPD query."""
        owned = self.owned_files()
        remaining = []
        for filename in candidates:
            expected = owned.get(filename)
            path = self.music / filename
            if expected is None:
                continue  # Unowned, missing or replaced: never delete it.
            if filename in playlist:
                remaining.append(filename)
            elif (
                path.resolve().is_relative_to(self.root) and identity(path) == expected
            ):
                path.unlink()
        return remaining
