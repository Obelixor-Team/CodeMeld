# Copyright (c) 2025 skum

from unittest.mock import MagicMock, patch

from src.ui import LiveUI


class TestLiveUI:
    def test_start_no_progress_bar(self, capsys):
        ui = LiveUI(total_files=10)
        ui.progress_style = "none"
        ui.verbose = True
        ui.start()
        captured = capsys.readouterr()
        assert "Processing 10 files..." in captured.out

    def test_start_ascii_progress_bar(self):
        with (
            patch("src.ui.tqdm") as mock_tqdm,
            patch("shutil.get_terminal_size", return_value=MagicMock(columns=80)),
        ):
            ui = LiveUI(total_files=10)
            ui.progress_style = "ascii"
            with patch("sys.stdout.isatty", return_value=True):
                ui.start()
            mock_tqdm.assert_called_with(
                total=10,
                desc="Processing files",
                ncols=80,
                leave=False,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
                ascii=True,
            )

    def test_start_block_progress_bar(self):
        with (
            patch("src.ui.tqdm") as mock_tqdm,
            patch("shutil.get_terminal_size", return_value=MagicMock(columns=80)),
        ):
            ui = LiveUI(total_files=10)
            ui.progress_style = "block"
            with patch("sys.stdout.isatty", return_value=True):
                ui.start()
            mock_tqdm.assert_called_with(
                total=10,
                desc="Processing files",
                ncols=80,
                leave=False,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]",
            )

    def test_start_verbose_non_tty(self, capsys):
        with patch("sys.stdout.isatty", return_value=False):
            ui = LiveUI(total_files=10)
            ui.verbose = True
            ui.start()
            captured = capsys.readouterr()
            assert "Processing 10 files..." in captured.out


class TestLiveUIUpdate:
    def test_update_skipped(self):
        ui = LiveUI()
        ui.update("file.txt", skipped=True)
        assert ui.processed == 0
        assert ui.skipped == 1

    def test_update_no_tokens_lines(self):
        ui = LiveUI()
        ui.update("file.txt", tokens=None, lines=None)
        assert ui.tokens == 0
        assert ui.total_lines == 0


class TestLiveUIFinish:
    def test_finish_list_files(self, capsys):
        ui = LiveUI()
        ui.list_files = True
        ui._included_files_set = {"file1.txt", "file2.txt"}
        ui.included_files = ["file1.txt", "file2.txt"]
        ui.finish()
        captured = capsys.readouterr()
        assert "Included files:" in captured.out
        assert "- file1.txt" in captured.out
        assert "- file2.txt" in captured.out

    def test_finish_summary_no_tokens(self, capsys):
        ui = LiveUI()
        ui.summary = True
        ui.count_tokens = False
        ui.finish()
        captured = capsys.readouterr()
        assert "Token count" not in captured.out

    def test_finish_no_psutil(self, capsys):
        with patch("src.ui._psutil_module", None):
            ui = LiveUI()
            ui.summary = True
            ui.finish()
            captured = capsys.readouterr()
            assert "Peak memory usage" not in captured.out
