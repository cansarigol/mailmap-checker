from pathlib import Path
from unittest.mock import MagicMock, patch

from mailmap_checker.git import get_identities, get_mailmap_file_config
from mailmap_checker.models import Identity


class TestGetIdentities:
    @patch("subprocess.run")
    def test_parses_valid_identities(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout=(
                "Alice Johnson <alice@acme.com>\n"
                "Alice Johnson <alice@acme.com>\n"
                "Bob Smith <bob@acme.com>\n"
                "Bob Smith <bob@acme.com>\n"
            )
        )
        identities = get_identities()
        assert identities == {
            Identity("Alice Johnson", "alice@acme.com"),
            Identity("Bob Smith", "bob@acme.com"),
        }

    @patch("subprocess.run")
    def test_includes_committer_identities(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout=("Alice <alice@acme.com>\nCommitter <committer@acme.com>\n")
        )
        identities = get_identities()
        assert Identity("Alice", "alice@acme.com") in identities
        assert Identity("Committer", "committer@acme.com") in identities

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
        assert cmd == ["git", "log", "--format=%an <%ae>%n%cn <%ce>"]

    @patch("subprocess.run")
    def test_with_git_dir(self, mock_run):
        mock_run.return_value = MagicMock(stdout="")
        get_identities(Path("/repo"))
        cmd = mock_run.call_args[0][0]
        assert cmd == [
            "git",
            "-C",
            str(Path("/repo")),
            "log",
            "--format=%an <%ae>%n%cn <%ce>",
        ]


class TestGetMailmapFileConfig:
    @patch("subprocess.run")
    def test_returns_configured_path(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="/custom/.mailmap\n")
        assert get_mailmap_file_config() == "/custom/.mailmap"

    @patch("subprocess.run")
    def test_returns_none_when_not_configured(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert get_mailmap_file_config() is None

    @patch("subprocess.run")
    def test_returns_none_for_empty_value(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="  \n")
        assert get_mailmap_file_config() is None

    @patch("subprocess.run")
    def test_with_git_dir(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="/p/.mailmap\n")
        get_mailmap_file_config(Path("/repo"))
        cmd = mock_run.call_args[0][0]
        assert cmd == ["git", "-C", str(Path("/repo")), "config", "mailmap.file"]

    @patch("subprocess.run")
    def test_without_git_dir(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        get_mailmap_file_config()
        cmd = mock_run.call_args[0][0]
        assert cmd == ["git", "config", "mailmap.file"]
