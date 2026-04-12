import pytest

from mailmap_checker.models import Identity
from mailmap_checker.parser import _MAX_FILE_SIZE, _MAX_LINE_LENGTH, parse_mailmap


class TestParseMailmap:
    def test_full_entry(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice Johnson <alice@acme.com> alice.j <alice@oldcorp.com>\n"
        )
        entries = parse_mailmap(mailmap)
        assert len(entries) == 1
        assert entries[0].canonical == Identity("Alice Johnson", "alice@acme.com")
        assert entries[0].alias == Identity("alice.j", "alice@oldcorp.com")

    def test_email_only_alias(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice Johnson <alice@acme.com> <alice@oldcorp.com>\n")
        entries = parse_mailmap(mailmap)
        assert len(entries) == 1
        assert entries[0].alias == Identity("", "alice@oldcorp.com")

    def test_canonical_only(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("Alice Johnson <alice@acme.com>\n")
        entries = parse_mailmap(mailmap)
        assert len(entries) == 1
        assert entries[0].canonical == Identity("Alice Johnson", "alice@acme.com")
        assert entries[0].alias == Identity("", "alice@acme.com")

    def test_skips_comments_and_blank_lines(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("# comment\n\nAlice <a@x.com> Bob <b@x.com>\n  \n")
        entries = parse_mailmap(mailmap)
        assert len(entries) == 1

    def test_nonexistent_file(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        assert parse_mailmap(mailmap) == []

    def test_invalid_line_without_angles(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("invalid line without angles\n")
        assert parse_mailmap(mailmap) == []

    def test_multiple_entries(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text("A <a@x.com> B <b@x.com>\nC <c@x.com> D <d@x.com>\n")
        entries = parse_mailmap(mailmap)
        assert len(entries) == 2

    def test_skips_entry_with_malicious_name(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "<script> <evil@x.com> Old <old@x.com>\n"
            "Alice <alice@x.com> Bob <bob@x.com>\n"
        )
        entries = parse_mailmap(mailmap)
        assert len(entries) == 1
        assert entries[0].canonical.name == "Alice"

    def test_skips_entry_with_invalid_email(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_text(
            "Alice <not-an-email> Bob <bob@x.com>\n"
            "Valid <valid@x.com> Old <old@x.com>\n"
        )
        entries = parse_mailmap(mailmap)
        assert len(entries) == 1
        assert entries[0].canonical.name == "Valid"

    def test_rejects_oversized_file(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        mailmap.write_bytes(b"x" * (_MAX_FILE_SIZE + 1))
        with pytest.raises(ValueError, match="exceeds maximum size"):
            parse_mailmap(mailmap)

    def test_skips_oversized_lines(self, tmp_path):
        mailmap = tmp_path / ".mailmap"
        long_name = "A" * _MAX_LINE_LENGTH
        mailmap.write_text(
            f"{long_name} <long@x.com> Old <old@x.com>\n"
            "Alice <alice@x.com> Bob <bob@x.com>\n"
        )
        entries = parse_mailmap(mailmap)
        assert len(entries) == 1
        assert entries[0].canonical.name == "Alice"
