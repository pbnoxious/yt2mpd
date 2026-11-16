"""Offline security contracts at the CLI and subprocess boundaries."""

import contextlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from yt2mpd import yt2mpd as app
from yt2mpd.config import Config


class Commands:
    """Replace external processes, but use real temporary media files."""

    def __init__(self):
        self.calls = []
        self.title = '1-$(touch PWNED)-`id`-"title".ogg'
        self.playlist = []
        self.fail = None
        self.reported_path = None
        self.queue_on_add = False
        self.created = []

    def run(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if not isinstance(args, list):
            raise TypeError("External commands must be argument lists")
        if self.fail and self.fail in args:
            if kwargs.get("check"):
                raise subprocess.CalledProcessError(1, args)
            return subprocess.CompletedProcess(args, 1, "", "MPD unavailable")
        if args[0] == "yt-dlp":
            target = Path(args[args.index("-o") + 1]).parent / self.title
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("audio", encoding="utf-8")
            self.created.append(target)
            reported = str(self.reported_path or target)
            if "--print" in args:
                stdout = json.dumps(reported) + "\n"
            else:
                stdout = f'[Metadata] Adding metadata to "{reported}"\n'
        elif "add" in args:
            if self.queue_on_add:
                self.playlist.append(args[-1])
            stdout = ""
        elif "playlist" in args:
            stdout = "\n".join(self.playlist)
        elif any("listall" in arg for arg in args):
            stdout = "Artist\nTitle\n"
        else:
            stdout = ""
        return subprocess.CompletedProcess(args, 0, stdout, "")

    def popen(self, args, **kwargs):
        result = self.run(args, **kwargs)

        class Process:
            returncode = result.returncode

            def communicate(self):
                return result.stdout.encode(), b""

        return Process()


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.music = Path(self.directory.name) / "Music"
        self.music.mkdir()
        self.tmp = self.music / "youtube"
        self.tmp.mkdir()
        self.config = Path(self.directory.name) / "yt2mpd.conf"
        self.write_config()
        self.commands = Commands()
        for target, replacement in (
            ("subprocess.run", self.commands.run),
            ("subprocess.Popen", self.commands.popen),
        ):
            mock = patch(target, side_effect=replacement)
            mock.start()
            self.addCleanup(mock.stop)
        self.system = patch("os.system").start()
        self.addCleanup(patch.stopall)
        output = contextlib.redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def write_config(self, tmp="youtube"):
        self.config.write_text(
            f"[yt2mpd]\nmusic_dir = {self.music}\ntmp_dir = {tmp}\n",
            encoding="utf-8",
        )

    def main(self, *options):
        with patch("sys.argv", ["yt2mpd", "-c", str(self.config), *options, "video"]):
            return app.main()

    def download(self):
        return app.download("video", str(self.music), "youtube")

    def test_media_names_remain_literal_subprocess_arguments(self):
        self.main()
        self.assertEqual(self.system.call_count, 0, "No command may use a shell")
        add = next(args for args, _ in self.commands.calls if "add" in args)
        self.assertEqual(Path(add[-1]).name, self.commands.title)
        for args, kwargs in self.commands.calls:
            self.assertIsInstance(args, list)
            self.assertFalse(kwargs.get("shell", False))

    def test_playlist_paths_cannot_escape(self):
        outside = Path(self.directory.name) / "escape"
        for suffix in (str(outside), "../escape", "../../escape", "%2e%2e%2fescape"):
            with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                app.download(
                    "https://example.invalid/watch?list=" + suffix,
                    str(self.music),
                    "youtube",
                )
        self.assertFalse(outside.exists())
        self.assertEqual(self.commands.calls, [])

    def test_config_rejects_absolute_traversal_and_symlink_escape(self):
        outside = Path(self.directory.name) / "outside"
        outside.mkdir()
        (self.music / "linked").symlink_to(outside, target_is_directory=True)
        for tmp in (str(outside), "../outside", "nested/../../outside", ".", "linked"):
            with self.subTest(tmp=tmp):
                self.write_config(tmp)
                with self.assertRaises(ValueError):
                    Config(str(self.config))

    def test_prune_keeps_unowned_files(self):
        unrelated = self.tmp / "personal.ogg"
        unrelated.write_text("keep", encoding="utf-8")
        owned = [self.music / name for name in self.download()]
        self.main("--prune")
        self.assertTrue(unrelated.exists(), "Unowned files must never be pruned")
        self.assertTrue(all(not path.exists() for path in owned))

    def test_playlist_failure_aborts_cleanup(self):
        owned = [self.music / name for name in self.download()]
        self.commands.fail = "playlist"
        with self.assertRaises(subprocess.CalledProcessError):
            self.main("--prune")
        self.assertTrue(all(path.exists() for path in owned))

    def test_queued_downloads_survive_pruning(self):
        owned = [self.music / name for name in self.download()]
        self.commands.playlist = [str(path.relative_to(self.music)) for path in owned]
        self.main("--prune")
        self.assertTrue(all(path.exists() for path in owned))

    def test_replacements_and_symlinks_are_not_owned(self):
        for kind in ("edited", "replacement", "symlink", "hardlink"):
            with self.subTest(kind=kind):
                target = self.music / self.download()[0]
                outside = Path(self.directory.name) / (kind + ".ogg")
                outside.write_text("personal", encoding="utf-8")
                if kind == "edited":
                    target.write_text("modified", encoding="utf-8")
                else:
                    target.unlink()
                    if kind == "replacement":
                        target.write_text("replacement", encoding="utf-8")
                    elif kind == "symlink":
                        target.symlink_to(outside)
                    else:
                        target.hardlink_to(outside)
                self.main("--prune")
                self.assertTrue(target.exists())
                self.assertEqual(outside.read_text(encoding="utf-8"), "personal")

    def test_downloader_cannot_claim_files_outside_its_batch(self):
        outside = self.tmp / "personal.ogg"
        outside.write_text("keep", encoding="utf-8")
        self.commands.reported_path = outside
        with self.assertRaises(ValueError):
            self.download()
        self.assertEqual(outside.read_text(encoding="utf-8"), "keep")
        unreceipted = self.commands.created[-1]
        self.commands.reported_path = None
        self.main("--prune")
        self.assertTrue(outside.exists())
        self.assertTrue(unreceipted.exists(), "Failed downloads are not owned")

    def test_other_mpc_failures_prevent_delete(self):
        for command in ("update", "add", "listall", "idle"):
            with self.subTest(command=command):
                self.commands.fail = command
                self.commands.queue_on_add = True
                with self.assertRaises(subprocess.CalledProcessError):
                    self.main("--delete")
                self.assertTrue(self.commands.created)
                self.assertTrue(all(path.exists() for path in self.commands.created))
        self.assertEqual(self.system.call_count, 0)

    def test_valid_playlist_and_option_like_identifier_stay_data(self):
        for identifier in (
            "https://example.invalid/watch?v=id&list=PL_123-abc",
            "--exec=id",
        ):
            with self.subTest(identifier=identifier):
                app.download(identifier, str(self.music), "youtube")
                args, _ = self.commands.calls[-1]
                self.assertEqual(args[-2:], ["--", identifier])
                self.assertIn("--ignore-config", args)

    def test_failed_download_does_not_enqueue_or_delete_anything(self):
        owned = [self.music / name for name in self.download()]
        self.commands.calls.clear()
        self.commands.fail = "yt-dlp"
        with self.assertRaises(subprocess.CalledProcessError):
            self.main("--delete")
        self.assertTrue(all(path.exists() for path in owned))
        self.assertFalse(any(args[0] == "mpc" for args, _ in self.commands.calls))

    def test_delete_removes_only_the_completed_download(self):
        unrelated = self.tmp / "personal.ogg"
        unrelated.write_text("keep", encoding="utf-8")
        self.main("--delete")
        self.assertTrue(self.commands.created)
        self.assertTrue(all(not path.exists() for path in self.commands.created))
        self.assertTrue(unrelated.exists())

    def test_invalid_receipt_aborts_before_any_deletion(self):
        owned = [self.music / name for name in self.download()]
        second = self.music / self.download()[0]
        receipt = second.parent / ".yt2mpd.json"
        receipt.write_text(json.dumps({"../personal.ogg": [1, 2, 3]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.main("--prune")
        self.assertTrue(all(path.exists() for path in [*owned, second]))

    def test_deletion_is_off_by_default(self):
        settings = Config(str(self.config))
        self.assertFalse(settings.prune)
        self.assertFalse(settings.delete)
        unrelated = self.tmp / "personal.ogg"
        unrelated.write_text("keep", encoding="utf-8")
        self.main()
        self.assertTrue(unrelated.exists())
        self.assertFalse(any("playlist" in args for args, _ in self.commands.calls))


if __name__ == "__main__":
    unittest.main()
