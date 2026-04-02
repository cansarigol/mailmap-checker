from pathlib import Path
from unittest.mock import MagicMock, patch

from mailmap_checker.git import get_identities
from mailmap_checker.models import Identity


class TestGetIdentities:
    @patch("subprocess.run")
    def test_parses_valid_identities(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Alice Johnson <alice@acme.com>\nBob Smith <bob@acme.com>\n"
        )
        identities = get_identities()
        assert identities == {
            Identity("Alice Johnson", "alice@acme.com"),
            Identity("Bob Smith", "bob@acme.com"),
        }

    @patch("subprocess.run")
    def test_deduplicates(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Alice <alice@acme.com>\nAlice <alice@acme.com>\n"
        )
        assert len(get_identities()) == 1

    @patch("subprocess.run")
    def test_skips_invalid_lines(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Alice <alice@acme.com>\ninvalid line\n"
        )
        identities = get_identities()
        assert len(identities) == 1
        assert Identity("Alice", "alice@acme.com") in identities

    @patch("subprocess.run")
    def test_skips_malicious_name(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="<script>alert(1)</script> <evil@example.com>\n"
            "Alice <alice@acme.com>\n"
        )
        identities = get_identities()
        assert len(identities) == 1
        assert Identity("Alice", "alice@acme.com") in identities

    @patch("subprocess.run")
    def test_skips_invalid_email(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Alice <not-an-email>\nBob <bob@acme.com>\n"
        )
        identities = get_identities()
        assert len(identities) == 1

    @patch("subprocess.run")
    def test_skips_blank_lines(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Alice <alice@acme.com>\n  \nBob <bob@acme.com>\n"
        )
        assert len(get_identities()) == 2

    @patch("subprocess.run")
    def test_empty_output(self, mock_run):
        mock_run.return_value = MagicMock(stdout="")
        assert get_identities() == set()

    @patch("subprocess.run")
    def test_without_git_dir(self, mock_run):
        mock_run.return_value = MagicMock(stdout="")
        get_identities()
        cmd = mock_run.call_args[0][0]
        assert cmd == ["git", "log", "--format=%an <%ae>"]

    @patch("subprocess.run")
    def test_with_git_dir(self, mock_run):
        mock_run.return_value = MagicMock(stdout="")
        get_identities(Path("/repo"))
        cmd = mock_run.call_args[0][0]
        assert cmd == ["git", "-C", str(Path("/repo")), "log", "--format=%an <%ae>"]
