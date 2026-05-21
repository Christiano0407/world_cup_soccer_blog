import sys
from unittest.mock import patch

import pytest

from worker.cli import main


class TestCliArgs:
    def test_no_args_exits(self):
        testargs = ["fifa-worker"]
        with pytest.raises(SystemExit) as exc:
            sys.argv = testargs
            main()
        assert exc.value.code == 1

    def test_help_flag(self):
        testargs = ["fifa-worker", "--help"]
        with pytest.raises(SystemExit) as exc:
            sys.argv = testargs
            main()
        assert exc.value.code == 0

    @patch("worker.cli.run_ingest")
    def test_ingest_flag(self, mock_run):
        testargs = ["fifa-worker", "--ingest"]
        sys.argv = testargs
        main()
        mock_run.assert_called_once()

    @patch("worker.cli.run_clean")
    def test_clean_flag(self, mock_run):
        testargs = ["fifa-worker", "--clean"]
        sys.argv = testargs
        main()
        mock_run.assert_called_once()

    @patch("worker.cli.run_load")
    def test_load_flag(self, mock_run):
        testargs = ["fifa-worker", "--load"]
        sys.argv = testargs
        main()
        mock_run.assert_called_once()

    @patch("worker.cli.run_analysis")
    def test_analysis_flag(self, mock_run):
        testargs = ["fifa-worker", "--analysis"]
        sys.argv = testargs
        main()
        mock_run.assert_called_once()

    @patch("worker.cli.run_ingest")
    @patch("worker.cli.run_clean")
    @patch("worker.cli.run_load")
    @patch("worker.cli.run_analysis")
    def test_all_flag(self, mock_analysis, mock_load, mock_clean, mock_ingest):
        testargs = ["fifa-worker", "--all"]
        sys.argv = testargs
        main()
        mock_ingest.assert_called_once()
        mock_clean.assert_called_once()
        mock_load.assert_called_once()
        mock_analysis.assert_called_once()

    @patch("worker.cli.run_ingest")
    @patch("worker.cli.run_clean")
    def test_ingest_clean_combo(self, mock_clean, mock_ingest):
        testargs = ["fifa-worker", "--ingest", "--clean"]
        sys.argv = testargs
        main()
        mock_ingest.assert_called_once()
        mock_clean.assert_called_once()
