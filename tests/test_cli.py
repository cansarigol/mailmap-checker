from unittest.mock import patch

import pytest

from mailmap_checker.cli import main, run
from mailmap_checker.models import Identity


class TestMain:
    @patch("sys.argv", ["mailmap-checker"])
    def test_exits_with_code(self):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


class TestRunNoCommand:
    def test_prints_help_and_returns_one(self, capsys):
        assert run([]) == 1
        output = capsys.readouterr().out
        assert "usage" in output.lower()


class TestCheck:
    @patch("mailmap_checker.cli.get_identities")
    def test_no_gaps(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        result = run(["check", "--mailmap", str(mailmap)])
        assert result == 0
        assert "properly mapped" in capsys.readouterr().out

    @patch("mailmap_checker.cli.get_identities")
    def test_with_gaps(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"),
            Identity("Alice", "alice@oldcorp.com"),
        }
        result = run(["check", "--mailmap", str(mailmap)])
        assert result == 1
        output = capsys.readouterr().out
        assert "unmapped" in output
        assert "dry-run" in output

    @patch("mailmap_checker.cli.get_identities")
    def test_default_mailmap_path(self, mock_get):
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        result = run(["check"])
        assert result == 0

    @patch("mailmap_checker.cli.get_identities")
    def test_git_dir_resolves_mailmap(self, mock_get, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        mailmap = repo / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        result = run(["check", "--git-dir", str(repo)])
        assert result == 0
        mock_get.assert_called_once_with(repo)

    @patch("mailmap_checker.cli.get_identities")
    def test_explicit_mailmap_overrides_git_dir(self, mock_get, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        custom = tmp_path / "custom.mailmap"
        custom.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        result = run(
            [
                "check",
                "--git-dir",
                str(repo),
                "--mailmap",
                str(custom),
            ]
        )
        assert result == 0


class TestInit:
    @patch("mailmap_checker.cli.get_identities")
    def test_creates_new_file(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        run(["init", "--mailmap", str(mailmap)])
        assert mailmap.exists()
        output = capsys.readouterr().out
        assert "Created" in output

    @patch("mailmap_checker.cli.get_identities")
    def test_existing_file(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("# existing\n")
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        run(["init", "--mailmap", str(mailmap)])
        output = capsys.readouterr().out
        assert "already exists" in output

    @patch("mailmap_checker.cli.get_identities")
    def test_returns_check_result(self, mock_get, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"),
            Identity("Alice", "alice@oldcorp.com"),
        }
        result = run(["init", "--mailmap", str(mailmap)])
        assert result == 1

    @patch("mailmap_checker.cli.get_identities")
    def test_git_dir_creates_mailmap_in_repo(self, mock_get, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        run(["init", "--git-dir", str(repo)])
        assert (repo / ".mailmap").exists()


class TestFix:
    @patch("mailmap_checker.cli.get_identities")
    def test_no_fixes_needed(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com")}
        result = run(["fix", "--mailmap", str(mailmap)])
        assert result == 0
        assert "No fixes needed" in capsys.readouterr().out

    @patch("mailmap_checker.cli.get_identities")
    def test_dry_run(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"),
            Identity("Alice", "alice@oldcorp.com"),
        }
        result = run(["fix", "--mailmap", str(mailmap), "--dry-run"])
        assert result == 1
        output = capsys.readouterr().out
        assert "Suggested" in output

    @patch("mailmap_checker.cli.get_identities")
    def test_apply_fixes(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"),
            Identity("Alice", "alice@oldcorp.com"),
        }
        result = run(["fix", "--mailmap", str(mailmap)])
        assert result == 0
        output = capsys.readouterr().out
        assert "Added" in output
        assert mailmap.read_text().strip() != ""

    @patch("mailmap_checker.cli.get_identities")
    def test_git_dir_with_fix(self, mock_get, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        mailmap = repo / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"),
            Identity("Alice", "alice@oldcorp.com"),
        }
        result = run(["fix", "--git-dir", str(repo)])
        assert result == 0
        assert mailmap.read_text().strip() != ""
