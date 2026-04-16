from unittest.mock import patch

import pytest

from mailmap_checker.cli import _collect_entries, main, run
from mailmap_checker.models import Identity


class TestCollectEntries:
    def test_reads_from_mailmap_file(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> Bob <bob@x.com>\n")
        entries = _collect_entries(mailmap, None)
        assert len(entries) == 1
        assert entries[0].canonical == Identity("Alice", "alice@x.com")

    def test_merges_root_mailmap(self, tmp_path):
        custom = tmp_path / "custom.mailmap"
        custom.write_text("Alice <alice@x.com> Bob <bob@x.com>\n")
        root = tmp_path / ".mailmap"
        root.write_text("Carol <carol@x.com> Dave <dave@x.com>\n")
        entries = _collect_entries(custom, tmp_path)
        assert len(entries) == 2

    def test_does_not_duplicate_when_same_path(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> Bob <bob@x.com>\n")
        entries = _collect_entries(mailmap, tmp_path)
        assert len(entries) == 1

    @patch("mailmap_checker.cli.get_mailmap_blob_config", return_value="HEAD:.mailmap")
    @patch(
        "mailmap_checker.cli.read_mailmap_blob",
        return_value="Carol <carol@x.com> Dave <dave@x.com>\n",
    )
    def test_merges_blob(self, _mock_blob, _mock_cfg, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> Bob <bob@x.com>\n")
        entries = _collect_entries(mailmap, tmp_path)
        assert len(entries) == 2

    @patch("mailmap_checker.cli.get_mailmap_blob_config", return_value=None)
    def test_no_blob_config(self, _mock_cfg, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> Bob <bob@x.com>\n")
        entries = _collect_entries(mailmap, tmp_path)
        assert len(entries) == 1

    @patch("mailmap_checker.cli.get_mailmap_blob_config", return_value="HEAD:.mailmap")
    @patch("mailmap_checker.cli.read_mailmap_blob", return_value=None)
    def test_blob_read_failure(self, _mock_blob, _mock_cfg, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> Bob <bob@x.com>\n")
        entries = _collect_entries(mailmap, tmp_path)
        assert len(entries) == 1


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
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_no_gaps(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        result = run(["check", "--mailmap", str(mailmap)])
        assert result == 0
        assert "properly mapped" in capsys.readouterr().out

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_with_gaps(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"): 10,
            Identity("alice.j", "alice@acme.com"): 3,
        }
        result = run(["check", "--mailmap", str(mailmap)])
        assert result == 1
        output = capsys.readouterr().out
        assert "unmapped" in output
        assert "commits)" in output
        assert "name heuristic" in output
        assert "start with a letter" in output
        assert "--by-commit-count" in output

    @patch("mailmap_checker.cli.get_mailmap_file_config", return_value=None)
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_default_mailmap_path(self, mock_get, _mock_cfg):
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        result = run(["check"])
        assert result == 0

    @patch("mailmap_checker.cli.get_mailmap_file_config", return_value=None)
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_git_dir_resolves_mailmap(self, mock_get, _mock_cfg, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        mailmap = repo / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        result = run(["check", "--git-dir", str(repo)])
        assert result == 0
        mock_get.assert_called_once_with(repo)

    @patch("mailmap_checker.cli.get_mailmap_file_config", return_value=None)
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_explicit_mailmap_overrides_git_dir(self, mock_get, _mock_cfg, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        custom = tmp_path / "custom.mailmap"
        custom.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
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

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_mailmap_file_config_used_when_no_explicit_path(self, mock_get, tmp_path):
        custom = tmp_path / "configured.mailmap"
        custom.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        with patch(
            "mailmap_checker.cli.get_mailmap_file_config",
            return_value=str(custom),
        ):
            result = run(["check"])
        assert result == 0

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_explicit_mailmap_overrides_config(self, mock_get, tmp_path):
        configured = tmp_path / "configured.mailmap"
        configured.write_text("should not be used")
        explicit = tmp_path / "explicit.mailmap"
        explicit.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        with patch(
            "mailmap_checker.cli.get_mailmap_file_config",
            return_value=str(configured),
        ):
            result = run(["check", "--mailmap", str(explicit)])
        assert result == 0

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_no_local_part_matching_flag(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice Johnson", "alice.johnson@acme.com"): 10,
            Identity("Alice Johnson", "alice.johnson@oldcorp.com"): 5,
        }
        assert run(["check", "--mailmap", str(mailmap)]) == 1
        assert (
            run(["check", "--mailmap", str(mailmap), "--no-local-part-matching"]) == 0
        )

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_by_commit_count_flag(self, mock_counts, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        id_few = Identity("jdoe", "shared@example.com")
        id_many = Identity("Jane Doe", "shared@example.com")
        mock_counts.return_value = {id_few: 100, id_many: 5}
        result = run(["check", "--mailmap", str(mailmap), "--by-commit-count"])
        assert result == 1
        output = capsys.readouterr().out
        assert "highest commit count" in output
        assert "(100 commits)" in output
        assert "(5 commits)" in output
        # With commit count, jdoe (100 commits) should be canonical
        assert "jdoe" in output.split("Canonical:")[1].split("\n")[0]
        # No tip about --by-commit-count when already using it
        assert "Tip:" not in output


class TestInit:
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_creates_new_file(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        run(["init", "--mailmap", str(mailmap)])
        assert mailmap.exists()
        output = capsys.readouterr().out
        assert "Created" in output

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_existing_file(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("# existing\n")
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        run(["init", "--mailmap", str(mailmap)])
        output = capsys.readouterr().out
        assert "already exists" in output

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_returns_check_result(self, mock_get, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"): 10,
            Identity("alice.j", "alice@acme.com"): 3,
        }
        result = run(["init", "--mailmap", str(mailmap)])
        assert result == 1

    @patch("mailmap_checker.cli.get_mailmap_file_config", return_value=None)
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_git_dir_creates_mailmap_in_repo(self, mock_get, _mock_cfg, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        run(["init", "--git-dir", str(repo)])
        assert (repo / ".mailmap").exists()


class TestFix:
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_no_fixes_needed(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {Identity("Alice", "alice@example.com"): 1}
        result = run(["fix", "--mailmap", str(mailmap)])
        assert result == 0
        assert "No fixes needed" in capsys.readouterr().out

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_dry_run(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"): 10,
            Identity("alice.j", "alice@acme.com"): 3,
        }
        result = run(["fix", "--mailmap", str(mailmap), "--dry-run"])
        assert result == 1
        output = capsys.readouterr().out
        assert "Suggested" in output
        assert "name heuristic" in output
        assert "--by-commit-count" in output

    @patch("mailmap_checker.cli.get_identity_counts")
    def test_apply_fixes(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"): 10,
            Identity("alice.j", "alice@acme.com"): 3,
        }
        result = run(["fix", "--mailmap", str(mailmap)])
        assert result == 0
        output = capsys.readouterr().out
        assert "Added" in output
        assert mailmap.read_text().strip() != ""

    @patch("mailmap_checker.cli.get_mailmap_file_config", return_value=None)
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_git_dir_with_fix(self, mock_get, _mock_cfg, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        mailmap = repo / ".mailmap"
        mailmap.write_text("")
        mock_get.return_value = {
            Identity("Alice", "alice@acme.com"): 10,
            Identity("alice.j", "alice@acme.com"): 3,
        }
        result = run(["fix", "--git-dir", str(repo)])
        assert result == 0
        assert mailmap.read_text().strip() != ""


class TestNormalize:
    def test_already_normalized(self, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@acme.com>\n")
        result = run(["normalize", "--mailmap", str(mailmap)])
        assert result == 0
        assert "Already normalized" in capsys.readouterr().out

    def test_applies_changes(self, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Bob <bob@x.com> old <bob@x.com>\nAlice <a@x.com>\n")
        result = run(["normalize", "--mailmap", str(mailmap)])
        assert result == 0
        assert "Normalized" in capsys.readouterr().out
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <a@x.com>"
        assert lines[1] == "Bob <bob@x.com>"

    def test_dry_run(self, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        original = "Bob <bob@x.com> old <bob@x.com>\n"
        mailmap.write_text(original)
        result = run(["normalize", "--mailmap", str(mailmap), "--dry-run"])
        assert result == 1
        assert "Normalized content" in capsys.readouterr().out
        assert mailmap.read_text() == original

    def test_missing_file(self, tmp_path, capsys):
        result = run(["normalize", "--mailmap", str(tmp_path / "nope")])
        assert result == 1
        assert "does not exist" in capsys.readouterr().out

    def test_stats_format1_collapses(self, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@x.com> old-alice <alice@x.com>\n"
            "Bob <bob@x.com> old-bob <bob@x.com>\n"
        )
        run(["normalize", "--mailmap", str(mailmap)])
        output = capsys.readouterr().out
        assert "2 same-email aliases collapsed to Format 1" in output
        assert "2 → 2 entries" in output

    def test_stats_duplicates_removed(self, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <alice@x.com> old <old@y.com>\nAlice <alice@x.com> old <old@y.com>\n"
        )
        run(["normalize", "--mailmap", str(mailmap)])
        output = capsys.readouterr().out
        assert "1 duplicate removed" in output
        assert "2 → 1 entries" in output

    def test_stats_in_dry_run(self, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice <alice@x.com> old <alice@x.com>\n")
        run(["normalize", "--mailmap", str(mailmap), "--dry-run"])
        output = capsys.readouterr().out
        assert "1 same-email alias collapsed to Format 1" in output
        assert "1 → 1 entries" in output

    @patch("mailmap_checker.cli.get_mailmap_file_config", return_value=None)
    def test_git_dir_resolves_mailmap(self, _mock_cfg, tmp_path, capsys):
        repo = tmp_path / "repo"
        repo.mkdir()
        mailmap = repo / ".mailmap"
        mailmap.write_text("Bob <bob@x.com> old <bob@x.com>\nAlice <a@x.com>\n")
        result = run(["normalize", "--git-dir", str(repo)])
        assert result == 0
        lines = mailmap.read_text().splitlines()
        assert lines[0] == "Alice <a@x.com>"
        assert lines[1] == "Bob <bob@x.com>"


class TestDisputedEmails:
    @patch("mailmap_checker.cli.get_identity_counts")
    def test_shared_email_with_different_canonicals(self, mock_get, tmp_path, capsys):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Person X <personx@acme.com> admin <shared@pc.local>\n"
            "Person Y <persony@acme.com> Person Y <shared@pc.local>\n"
        )
        mock_get.return_value = {
            Identity("Person X", "personx@acme.com"): 10,
            Identity("Person Y", "persony@acme.com"): 5,
            Identity("admin", "shared@pc.local"): 2,
            Identity("Person Y", "shared@pc.local"): 3,
        }
        result = run(["check", "--mailmap", str(mailmap)])
        assert result == 0
        assert "properly mapped" in capsys.readouterr().out
